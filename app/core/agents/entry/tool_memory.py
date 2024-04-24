from __future__ import annotations

import logging.config
from pathlib import Path

from langchain_core.tools import tool

from app.core.memory.log_search import LogMemoryAccessTool
from app.core.utils import setup_logger

from ..tool_interface import ToolTemplate

logger = setup_logger(__name__)


class MemoryAccessTool(ToolTemplate):

    def __init__(self):
        super().__init__()

    @tool("NEW_MEMORY_ACCESS_QUERY_RUNNER")
    def tool_func(self, query: str) -> str:
        """
        Generates an answer based on the logs and the provided query without explicitly calling the input.

        Args:
        query str : the query string to search in memory logs.

        Returns:
            str: the response generated based on the query.
        """

        logger.info(f"Searching logs for query: {query}")

        # Instantiate LogMemoryAccessTool with its default parameters
        memory_tool_instance = LogMemoryAccessTool()

        # Directly use the generated answer method since we're focusing on generating responses
        return memory_tool_instance.generate_answer(query_input=query)
