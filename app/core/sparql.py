from __future__ import annotations

from typing import Any, Dict, List, Optional

from RdfGraphCustom import RdfGraph
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts.base import BasePromptTemplate
from langchain_core.pydantic_v1 import Field

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains.base import Chain
from prompts import (
    SPARQL_GENERATION_SELECT_PROMPT,
)
from langchain.chains.llm import LLMChain
import re

import json
import csv
import tempfile
from pathlib import Path
import logging.config
import os

parent_dir = Path(__file__).parent.parent
config_path = parent_dir / "config" / "logging.ini"
logging.config.fileConfig(config_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)


##Question-answering against an RDF or OWL graph by generating SPARQL statements.
class GraphSparqlQAChain(Chain):

    graph: RdfGraph = Field(exclude=True)
    sparql_generation_select_chain: LLMChain
    input_key: str = "question"  #: :meta private:
    entities_key: str = "entities"  #: :meta private:
    output_key: str = "result"  #: :meta private:
    sparql_key: str = "sparql_query_used"  #: :meta private:

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        _output_keys = [self.output_key]
        return _output_keys

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        *,
        sparql_select_prompt: BasePromptTemplate = SPARQL_GENERATION_SELECT_PROMPT,
        **kwargs: Any,
    ) -> GraphSparqlQAChain:
        """
        Takes a language model and prompt template as input to create a
        GraphSparqlQAChain object.

        Args:
          cls: It is a conventional name used in class methods to refer to the class object.
          llm (BaseLanguageModel): The large language model (LLM) used to generate SPARQL queries.
          sparql_select_prompt (BasePromptTemplate): The prompt template used to generate SPARQL queries.

        Returns:
          GraphSparqlQAChain : A GraphSparqlQAChain object with the specified language model and prompt template.
        """
        sparql_generation_select_chain = LLMChain(
            llm=llm, prompt=sparql_select_prompt)

        return cls(
            sparql_generation_select_chain=sparql_generation_select_chain,
            **kwargs,
        )

    @staticmethod
    def remove_markdown_quotes(query_with_markdown: str) -> str:
        """
        removes markdown quotes from a given string.

        Args:
          query_with_markdown (str): input string

        Returns:
          str : cleaned input string without the markdown quotes.
        """
        txt = re.sub(r"```sparql", "", query_with_markdown)
        cleaned_query = re.sub(r"```", "", txt)

        return cleaned_query

    @staticmethod
    def remove_xsd_prefix(query):
        lines = query.split('\n')
        filtered_lines = [line for line in lines if not line.startswith("PREFIX xsd:")]
        updated_query = '\n'.join(filtered_lines)
        return updated_query

    @staticmethod
    def json_to_csv(json_data):
        """
        Converts JSON data into a CSV file and returns the path to the temporary
        CSV file.

        Args:
          json_data: the JSON data to be converted into a CSV file.

        Returns:
          str or None: the path to the temporary CSV file if the JSON data is not empty and is a list, otherwise None.
        """
        # Convert JSON data to Python list of dictionaries if it's a string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:  # Assume it's already a Python list of dictionaries
            data = json_data

        if data and isinstance(data, list):
            # Create a "kgbot" directory inside the system's temporary directory
            kgbot_temp_dir = os.path.join(tempfile.gettempdir(), "kgbot")
            os.makedirs(kgbot_temp_dir, exist_ok=True)  # Make the directory if it doesn't exist

            # Define the path for the new CSV file within the "kgbot" directory
            temp_csv_path = os.path.join(kgbot_temp_dir, tempfile.mktemp(suffix=".csv", dir=kgbot_temp_dir))

            # Create and open the file for writing
            with open(temp_csv_path, mode="w", newline="") as temp_file:
                # Extract headers from the first item, assuming all items are dictionaries
                headers = data[0].keys()
                # Create a CSV writer object
                csv_writer = csv.DictWriter(temp_file, fieldnames=headers)
                # Write the header
                csv_writer.writeheader()
                # Write the rows
                csv_writer.writerows(data)

            # The path to return will be the full path to the newly created CSV file within "kgbot"
            temp_file_path = temp_csv_path

        else:
            # Handle the case where data is empty or not a list
            logger.info("JSON data is empty or not in the expected format.")
            temp_file_path = None

        return temp_file_path


    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        """

        Query the Knowledge Graph after generating SPARQL query and return the results.

        Args:
          inputs (Dict[str, Any]): takes inputs in the form of a dictionary with keys `self.input_key` and `self.entities_key`.
          run_manager (Optional[CallbackManagerForChainRun]): an optional parameter of type `CallbackManagerForChainRun`. It is used to manage
        callbacks during the execution of the method.

        Returns:
          dict: A dictionary containing the contextualized sparql result.

        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        prompt = inputs[self.input_key]
        entities = inputs[self.entities_key]

        generated_sparql = self.sparql_generation_select_chain.run(
            {
                "question": prompt,
                "entities": entities,
                "schema": self.graph.get_schema
            },
            callbacks=callbacks,
        )

        # TODO [Franck]: why do we need this? The prompt explicitely says to NOT return any markdown, still there might be some?
        generated_sparql = self.remove_markdown_quotes(generated_sparql)
        generated_sparql = self.remove_xsd_prefix(generated_sparql)
        logger.debug("Generated SPARQL query (Removed xsd prefix after remove markdown prefix)): %s", generated_sparql)

        _run_manager.on_text("Generated SPARQL:",
                             end="\n", verbose=self.verbose)
        _run_manager.on_text(
            generated_sparql, color="green", end="\n", verbose=self.verbose
        )

        result = self.graph.query(generated_sparql)

        # creating csv temp file inside the _call

        temp_file_path = self.json_to_csv(result)
        
        logger.info("Saving results to file: %s", temp_file_path)

        # Convert the SPARQL query output to  a string if it's not already

        if isinstance(result, dict):  # Assuming result2 is a dictionary (JSON)
            result2_string = json.dumps(result)
        else:
            result2_string = str(
                result
            )  # Make sure it's a string if it's not a dictionary

        # Now call the token_counter method with the string count the tokens
        tokens_result = RdfGraph.token_counter(result2_string)
        tokens_question = RdfGraph.token_counter(prompt)
        tokens_query = RdfGraph.token_counter(generated_sparql)

        # Sum of tokens from different parts
        total_tokens = tokens_result + tokens_question + tokens_query

        # Define the LLM context window size
        llm_context_window = 10000

        # Check if the total token count exceeds the LLM's context window
        if total_tokens > llm_context_window:
            # If it exceeds, create a contextualized_result without the "result" field
            contextualized_result = {
                "query": generated_sparql,
                # "result" is omitted because the total token count exceeds the LLM context window
                "temp_file_path": temp_file_path,  # Add the file path to the results
            }
        else:
            contextualized_result = {
                "query": generated_sparql,
                # Include the result as the total token count is within the LLM context window
                "result": result,
                "temp_file_path": temp_file_path,  # Add the file path to the results
            }


        return {self.output_key: contextualized_result}
