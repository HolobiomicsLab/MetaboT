import importlib
import json
import logging
import logging.config
import os
from pathlib import Path
from typing import List, Optional, Type
from langchain.tools import BaseTool
import tiktoken


def setup_logger(name):
    """
    Set up logging configuration.

    Parameters:
    - name (str): Typically __name__ from the calling module.

    Returns:
    - logger (logging.Logger): Configured logger object.
    """
    # Resolve the path to the configuration file
    parent_dir = Path(__file__).resolve().parent.parent
    config_path = parent_dir / "config" / "logging.ini"

    # Configure logging
    logging.config.fileConfig(config_path, disable_existing_loggers=False)

    # Get and return the logger
    return logging.getLogger(name)


logger = setup_logger(__name__)


def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "config.json"
    with open(config_path, "r") as file:
        return json.load(file)


def import_tools(directory: str, module_prefix: str, **kwargs) -> List:
    """
    Imports all Python modules in a specified directory that inherit from BaseTool
    and returns a list of these tools.

    Args:
        directory (str): The directory to search for Python files.
        module_prefix (str): The prefix used to form the full Python import path.
        kwargs: Additional keyword arguments to pass to the tool's constructor. (for example llm and graph for sparql agent)

    Returns:
        List: A list of tools. Each tool is an instance of a function
             provided by the tool's module decorator (@tool)

    Raises:
        AttributeError, ImportError.

    Examples:
        >>> import_tools("app/core/agents/enpkg", "app.core.agents.enpkg")
    """
    tools = []
    for filename in filter(
        lambda f: f.startswith("tool_") and f.endswith(".py"), os.listdir(directory)
    ):
        module_name, module_path = (
            filename[:-3],
            f"{module_prefix}.{filename[:-3]}",
        )
        try:
            module = importlib.import_module(module_path)
            tool = find_tool_in_module(module, **kwargs)
            if tool:
                tools.append(tool)
                logger.info(f"Imported tool: {tool.name}")
            else:
                logger.warning(f"No valid BaseTool subclass found in {module_name}")
        except (AttributeError, ImportError) as e:
            logger.error(f"Failed to import {module_name}: {e}")
    return tools


def find_tool_in_module(module, **kwargs) -> Optional[Type[BaseTool]]:
    """
    Searches a given module for any class that is a subclass of BaseTool, but not BaseTool itself,
    and returns an instance of it if found.

    Args:
        module: The module to inspect.

    Returns:
        Optional[Type[BaseTool]]: An instance of the found subclass of BaseTool if any,
                                      None otherwise.
    """
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if (
            isinstance(attribute, type)
            and issubclass(attribute, BaseTool)
            and attribute is not BaseTool
        ):
            return attribute(**kwargs)
    return None


def get_module_prefix(name):
    """
    Extracts the module prefix based on the current file's __name__,
    excluding the last part to get the parent module path.

    Example:
    __name__ = "app.core.agents.enpkg.agent"
    get_module_prefix(__name__) -> "app.core.agents.enpkg"
    """
    current_module = name
    module_parts = current_module.split(".")
    return ".".join(module_parts[:-1])


def token_counter(text: str) -> int:
    tokenizer = tiktoken.encoding_for_model(model_name="gpt-4")
    # TODO [Franck]: the model name should be a config param
    tokens = tokenizer.encode(text)
    return len(tokens)
