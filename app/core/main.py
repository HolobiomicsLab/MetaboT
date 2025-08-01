import os
import argparse
from typing import Optional
from dotenv import load_dotenv
from langsmith import Client
from pathlib import Path
from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from app.core.utils import IntRange, setup_logger
import configparser
from langchain_community.chat_models import ChatOpenAI, ChatLiteLLM
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


def main():
    """Main function to run the workflow."""
    # Define command line arguments

    parser = argparse.ArgumentParser(description="Process a workflow with a predefined question number.")
    parser.add_argument('-q', '--question', type=int, choices=IntRange(1, len(standard_questions)),
                        help=f"Choose a standard question number from 1 to {len(standard_questions)}.")
    parser.add_argument('-c', '--custom', type=str,
                        help="Provide a custom question.")
    parser.add_argument('-e', '--evaluation', action='store_true',
                        help="Enable evaluation mode")
    parser.add_argument('--api-key', type=str,
                        help="OpenAI API key (optional, defaults to environment variable)")
    parser.add_argument('--endpoint', type=str,
                        help="Knowledge graph endpoint URL (optional)")

    args = parser.parse_args()

    if args.question:
        question = standard_questions[args.question - 1]
    elif args.custom:
        question = args.custom
    else:
        print("You must provide either a standard question number or a custom question.")
        return

    # Initialize LangSmith if available
    langsmith_client = langsmith_setup()

    # Get endpoint URL from arguments or environment
    endpoint_url = (
        args.endpoint
        or os.environ.get("KG_ENDPOINT_URL")
        or "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    )
    models = llm_creation()

    try:
        # Create and process workflow
        workflow = create_workflow(
            models=models,
            endpoint_url=endpoint_url,
            evaluation=False,
            api_key=args.api_key
        )

        process_workflow(workflow, question)

    except Exception as e:
        logger.error(f"Error processing workflow: {e}")
        raise


if __name__ == "__main__":
    main()
