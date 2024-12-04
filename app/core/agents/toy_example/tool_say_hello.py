from __future__ import annotations


from langchain.tools import BaseTool

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
from app.core.session import setup_logger
from langchain.pydantic_v1 import BaseModel, Field


logger = setup_logger(__name__)


class HelloInput(BaseModel):
    input: str = Field(description="string 'say hello please'")


class Interpreter(BaseTool):

    name: str = "SAY_HELLO_TOOL"
    description: str = """
    Say Hello to the user. 
    Args : 
        input str : 'say hello please'
        
    Returns:
        str : 'Hello'
    """

    args_schema = HelloInput

    def __init__(self):
        super().__init__()

    def _run(
        self,
        input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        hello_message = """
        #####################################################
        
        ?
        ?
        ?
        
        Hello
        
        ?
        ?
        ?
        
        #####################################################
        
        """
        return hello_message
