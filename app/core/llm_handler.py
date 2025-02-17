import os
from typing import Any, Dict, Optional
from langchain_community.chat_models import ChatOpenAI
from app.core.utils import setup_logger
import configparser
from pathlib import Path

logger = setup_logger(__name__)

def llm_creation(api_key: Optional[str] = None) -> Dict[str, ChatOpenAI]:
    """
    Create language models based on configuration parameters.

    Args:
        api_key (Optional[str]): The API key for OpenAI. If None, uses environment variable.

    Returns:
        Dict[str, ChatOpenAI]: A dictionary containing the language models.
    """
    config = configparser.ConfigParser()
    config_path = Path(__file__).resolve().parent.parent / "config" / "params.ini"
    logger.info(f"Loading configuration from {config_path}")
    config.read(config_path)

    sections = ["llm", "llm_preview", "llm_o", "llm_mini", "llm_o3_mini", "llm_o1"]
    models = {}

    # Get the OpenAI API key from the argument or environment variables
    openai_api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OpenAI API key not found in environment variables or parameters")

    for section in sections:
        temperature = config[section].getfloat("temperature", 0.0)
        model_id = config[section]["id"]
        max_retries = config[section].getint("max_retries", 3)
        
        llm = ChatOpenAI(
            temperature=temperature,
            model=model_id,
            max_retries=max_retries,
            verbose=True,
            openai_api_key=openai_api_key,
        )
        models[section] = llm

    return models