from __future__ import annotations


from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


from app.core.memory.log_search import LogMemoryAccessTool
from app.core.utils import setup_logger


logger = setup_logger(__name__)


class QueryInput(BaseModel):
    query: str = Field(description="Query string to search in memory logs.")


class MemoryAccessTool(BaseTool):
    name: str = "NEW_MEMORY_ACCESS_QUERY_RUNNER"
    description: str = """
    Generates an answer based on the logs and the provided query without explicitly calling the input.

    Args:
    query str : the query string to search in memory logs.

    Returns:
        str: the response generated based on the query.
    """
    args_schema = QueryInput

    def __init__(self):
        super().__init__()

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        logger.info(f"Searching logs for query: {query}")

        # Instantiate LogMemoryAccessTool with its default parameters
        memory_tool_instance = LogMemoryAccessTool()

        # Directly use the generated answer method since we're focusing on generating responses
        return memory_tool_instance.generate_answer(query_input=query)
