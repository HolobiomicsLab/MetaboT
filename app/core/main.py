import os
import shutil
import argparse
import configparser
from typing import Optional, List
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langchain_community.chat_models import ChatLiteLLM
from langchain_openai import ChatOpenAI

from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from app.core.session import create_user_session, initialize_session_context
from app.core.utils import IntRange, setup_logger
from app.core.questions import standard_questions


# Load environment variables
load_dotenv()
logger = setup_logger(__name__)

parent_dir = Path(__file__).resolve().parent.parent
graph_path = parent_dir / "graphs" / "graph.pkl"
params_path = parent_dir / "config" / "params.ini"


# Mapping of provider/model to environment variable names
API_KEY_MAPPING = {
    "deepseek": "DEEPSEEK_API_KEY",
    "ovh": "OVHCLOUD_API_KEY",
    "openai": "OPENAI_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "mistral": "MISTRAL_API_KEY"
}


class SessionFilePreparationError(ValueError):
    """Raised when CLI input files cannot be staged into the session directory."""

    def __init__(self, source_path: Path, message: str):
        super().__init__(message)
        self.source_path = source_path


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for specified provider from environment variables.

    Args:
        provider: Provider name matching a key in API_KEY_MAPPING

    Returns:
        API key if found, None otherwise
    """
    env_var = API_KEY_MAPPING.get(provider)
    return os.getenv(env_var) if env_var else None


def create_litellm_model(config: configparser.SectionProxy) -> ChatLiteLLM:
    """
    Create a ChatLiteLLM instance based on the model id and configuration.
    Only uses parameters that are explicitly specified in the configuration.

    Args:
        config (configparser.SectionProxy): The configuration section

    Returns:
        ChatLiteLLM: Configured ChatLiteLLM instance
    """
    if "id" not in config:
        raise ValueError("Model id is required in configuration")

    model_id = config["id"]

    model_name = model_id

    if model_id.startswith("deepseek"):
        provider = "deepseek"
    elif model_id.startswith("gpt"):
        provider = "openai"
        model_name = f"openai/{model_id}"
    elif model_id.startswith("huggingface"):
        provider = "huggingface"
    elif model_id.startswith("claude"):
        provider = "anthropic"
    elif model_id.startswith("gemini"):
        provider = "gemini"
    elif model_id.startswith("mistral"):
        provider = "mistral"

    api_key = get_api_key(provider)

    model_params = {
        "model": model_name,
        "api_key": api_key,
        "temperature": float(config.get("temperature", 0.0)),
        "max_retries": int(config.get("max_retries", 3))
    }

    for param in ["base_url", "api_base"]:
        if param in config:
            model_params[param] = config[param]

    return ChatLiteLLM(**model_params)


def llm_creation(api_key=None, params_file=None):
    """
    Reads the parameters from the configuration file (default is params.ini) and initializes the language models.

    Args:
        api_key (str, optional): The API key for the OpenAI API.
        params_file (str, optional): Path to an alternate configuration file.

    Returns:
        dict: A dictionary containing the language models.
    """

    config = configparser.ConfigParser()
    if params_file:
        config.read(params_file)
    else:
        config.read(params_path)

    models = {}

    for section in config.sections():
        if section.startswith("llm_litellm"):
            models[section] = create_litellm_model(config[section])
            continue

        temperature = config[section]["temperature"]
        model_id = config[section]["id"]
        max_retries = config[section]["max_retries"]

        provider = "openai"
        if section.startswith("deepseek"):
            provider = "deepseek"
        elif section.startswith("ovh"):
            provider = "ovh"

        if api_key is None:
            api_key = get_api_key(provider)

        model_params = {
            "temperature": float(temperature),
            "model": model_id,
            "max_retries": int(max_retries),
            "verbose": True
        }

        if "base_url" in config[section]:
            base_url = config[section]["base_url"]
            if provider == "deepseek":
                model_params["openai_api_base"] = base_url
                model_params["openai_api_key"] = api_key
            else:
                model_params["base_url"] = base_url
                model_params["api_key"] = api_key
        else:
            model_params["openai_api_key"] = api_key

        llm = ChatOpenAI(**model_params)
        models[section] = llm

    return models


def langsmith_setup() -> Optional[Client]:
    """
    Set up the LangSmith environment and client if an API key is present.

    Returns:
        Optional[Client]: LangSmith client if setup successful, None otherwise
    """
    # Check whether an API key is present
    api_key = os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")

    if not api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("No LangSmith API key found, LANGCHAIN_TRACING_V2 set to false.")
        return None

    # If an API key exists, enable V2 tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

    # Set default project if not already set
    os.environ["LANGCHAIN_PROJECT"] = (
        os.environ.get("LANGCHAIN_PROJECT")
        or os.environ.get("LANGSMITH_PROJECT")
        or "MetaboT"
    )

    # Set default endpoint if not already set
    os.environ["LANGCHAIN_ENDPOINT"] = (
        os.environ.get("LANGCHAIN_ENDPOINT")
        or os.environ.get("LANGSMITH_ENDPOINT")
        or os.environ.get("LANGSMITH_BASE_URL")
        or "https://api.smith.langchain.com"
    )

    try:
        client = Client(api_key=api_key)
        logger.info(f"Langchain client initialized: {client}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Langchain client: {e}")
        return None


def _prepare_session_files(session_id: str, file_paths: List[str]) -> Path:
    """
    Copy user-supplied local files into the session's input directory so that
    the FILE_ANALYZER tool can discover them at runtime.

    Args:
        session_id: Active session identifier.
        file_paths: List of local file paths provided via the CLI.

    Returns:
        Path to the session input directory.

    Raises:
        SessionFilePreparationError: If any supplied path cannot be staged safely.
    """
    input_dir = create_user_session(session_id, input_dir=True)
    staged_destinations: dict[Path, Path] = {}

    for raw_path in file_paths:
        src = Path(raw_path).expanduser().resolve(strict=False)
        if not src.exists():
            raise SessionFilePreparationError(src, f"File not found: {src}")
        if not src.is_file():
            raise SessionFilePreparationError(src, f"Input path is not a file: {src}")

        dest = input_dir / src.name
        previous_src = staged_destinations.get(dest)
        if previous_src is not None:
            if previous_src == src:
                raise SessionFilePreparationError(
                    src,
                    f"Input file was provided more than once: {src}",
                )
            raise SessionFilePreparationError(
                src,
                (
                    f"Cannot stage '{src}' because it would overwrite '{previous_src}' in "
                    f"the session input directory. Rename one of the files or choose a different path."
                ),
            )

        if src == dest.resolve(strict=False):
            raise SessionFilePreparationError(
                src,
                f"Input file is already staged in the session directory: {src}",
            )

        if dest.exists():
            raise SessionFilePreparationError(
                src,
                f"Cannot stage '{src}' because destination '{dest}' already exists.",
            )

        try:
            shutil.copy2(str(src), str(dest))
        except (shutil.SameFileError, OSError) as exc:
            raise SessionFilePreparationError(
                src,
                f"Failed to stage '{src}' into '{dest}': {exc}",
            ) from exc

        staged_destinations[dest] = src
        logger.info(f"Copied '{src}' -> '{dest}'")

    return input_dir


def main():
    """
    CLI entry-point for running the MetaboT workflow.

    Usage examples:
        python -m app.core.main -q 1
        python -m app.core.main -c "Describe my dataset" -f data.csv
        python -m app.core.main -c "Compare files" -f file1.csv file2.tsv
    """
    parser = argparse.ArgumentParser(
        description="Process a workflow with a predefined question number."
    )
    parser.add_argument(
        '-q', '--question', type=int,
        choices=IntRange(1, len(standard_questions)),
        help=f"Choose a standard question number from 1 to {len(standard_questions)}.",
    )
    parser.add_argument(
        '-c', '--custom', type=str,
        help="Provide a custom question.",
    )
    parser.add_argument(
        '-f', '--file', type=str, nargs='+',
        help="One or more local file paths to make available for the FILE_ANALYZER tool.",
    )
    parser.add_argument(
        '-e', '--evaluation', action='store_true',
        help="Enable evaluation mode.",
    )
    parser.add_argument(
        '--api-key', type=str,
        help="OpenAI API key (optional, defaults to environment variable).",
    )
    parser.add_argument(
        '--endpoint', type=str,
        help="Knowledge graph endpoint URL (optional).",
    )

    args = parser.parse_args()

    # Resolve the question
    if args.question:
        question = standard_questions[args.question - 1]
    elif args.custom:
        question = args.custom
    else:
        print("You must provide either a standard question number (-q) or a custom question (-c).")
        return

    # Create a user session (mirrors the Streamlit session lifecycle) and
    # reconfigure the logger so subsequent CLI logs land in the session file.
    session_id = create_user_session()
    initialize_session_context(session_id)
    global logger
    logger = setup_logger(__name__)

    # Initialize LangSmith if available
    langsmith_setup()

    # Resolve endpoint URL
    endpoint_url = (
        args.endpoint
        or os.environ.get("KG_ENDPOINT_URL")
        or "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    )

    # Initialize language models
    models = llm_creation(api_key=args.api_key)

    # Stage user-provided files into the session's input directory
    if args.file:
        try:
            _prepare_session_files(session_id, args.file)
        except SessionFilePreparationError as exc:
            logger.error(str(exc))
            print(f"Error: {exc}")
            return

    try:
        workflow = create_workflow(
            models=models,
            session_id=session_id,
            endpoint_url=endpoint_url,
            evaluation=False,
            api_key=args.api_key,
        )
        process_workflow(workflow, question)

    except Exception as e:
        logger.error(f"Error processing workflow: {e}")
        raise


if __name__ == "__main__":
    main()
