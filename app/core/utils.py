import importlib
import json
import logging
import logging.config
import os
from pathlib import Path
from typing import List, Optional, Type
from langchain.tools import BaseTool
import tiktoken
import inspect
import tempfile
from uuid import uuid4
from app.core.session import setup_logger

logger = setup_logger(__name__)


def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "langgraph.json"
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
        logger.info(f"Importing tool from {filename}")
        module_name, module_path = (
            filename[:-3],
            f"{module_prefix}.{filename[:-3]}",
        )
        logger.info(f"Module name: {module_name}")
        try:
            module = importlib.import_module(module_path)
            logger.info(f"Module path: {module_path}")
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
            # Inspect the constructor to determine the needed parameters
            constructor_signature = inspect.signature(attribute)
            constructor_params = constructor_signature.parameters

            # Prepare the arguments that the constructor can accept
            filtered_args = {k: v for k, v in kwargs.items() if k in constructor_params}

            # Create an instance of the tool with the filtered arguments
            return attribute(**filtered_args)

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


class IntRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.range = range(start, end + 1)

    def __contains__(self, item):
        return item in self.range

    def __iter__(self):
        # for help display
        return iter([f"[{self.start}, {self.end}]"])

    def __str__(self):
        return f"[{self.start}, {self.end}]"

    def __repr__(self):
        return self.__str__()
