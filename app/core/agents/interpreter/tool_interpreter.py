from __future__ import annotations

import logging.config
from pathlib import Path

from codeinterpreterapi import CodeInterpreterSession, File
from langchain_core.tools import tool

from app.core.utils import setup_logger

from ..tool_interface import ToolTemplate

logger = setup_logger(__name__)


class Interpreter(ToolTemplate):

    def __init__(self):
        super().__init__()

    @tool("INTERPRETER_TOOL")
    def tool_func(
        self, question: str, generated_sparql_query: str, file_path: str
    ) -> None:
        """Interprets the results of a SPARQL query based on user's question.
        The function takes an original user question, generated sparql query, and generated sparql query result stored in file_path and returns interpreted answer content

        Args:
            question (str): The original question from the user.
            generated_sparql_query (str): The generated SPARQL query.
            file_path (str): The file path where the result of the generated SPARQL query is stored.

        Returns:
            None: Outputs the response after interpreting the SPARQL results.
        """
        # context manager for start/stop of the session
        # define the user request
        logger.info(f"Interpreting {question}")
        logger.info(f"SPARQL query: {generated_sparql_query}")
        logger.info(f"File path: {file_path}")
        with CodeInterpreterSession() as session:
            user_request = f"""You are an interpreter agent. Your task is to analyze the output related to a SPARQL query, which could be in two forms:
            If the output of the Sparql_query_runner agent is only the dictionary containing question: "{question}", generated SPARQL query: "{generated_sparql_query}" which was used to query the knowledge graph to answer to the question and path: "{file_path}" containing the SPARQL output then you should review the provided dataset from the file and SPARQL query to provide a clear, concise answer to the question. Additionally, if visualization of the results is necessary (e.g., when the SPARQL output is large or complex), you should provide an appropriate visualization, such as a bar chart, diagram, or plot, to effectively communicate the answer.
            If the output of the Sparql_query_runner agent contains the answer to the question together with the dictionary containing the question: "{question}", generated SPARQL query: "{generated_sparql_query}" and path: "{file_path}", then you should analyze this output and provide visualization of the answer to the question. 
            The type of visualization – bar chart, diagram, or plot – will depend on the nature of the SPARQL output and the best way to represent the answer to the question clearly.
            Submit only the final answer to the supervisor. Indicate the format of the dataset for appropriate handling. """
            files = [
                File.from_path(file_path),
            ]

            # generate the response
            response = session.generate_response(user_request, files=files)
            # output the response (text + image)
            response.show()
            return response.content
