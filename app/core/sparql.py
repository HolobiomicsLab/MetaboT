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


class GraphSparqlQAChain(Chain):
    """Question-answering against an RDF or OWL graph by generating SPARQL statements."""

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
        Initializes a `GraphSparqlQAChain` object using a base language model (`BaseLanguageModel`) for SPARQL query generation.

        :param cls: Reference to the class itself, indicating the method belongs to the class.
        :param llm: An instance of `BaseLanguageModel`, utilized for generating natural language prompts for SPARQL query generation.
        :return: An instance of `GraphSparqlQAChain`.
        """
        sparql_generation_select_chain = LLMChain(llm=llm, prompt=sparql_select_prompt)

        return cls(
            sparql_generation_select_chain=sparql_generation_select_chain,
            **kwargs,
        )

    @staticmethod
    def remove_markdown_quotes(query_with_markdown):
        """
        The `remove_markdown_quotes` function removes markdown quotes from a given query.
        """
        txt = re.sub(r"```sparql", "", query_with_markdown)
        cleaned_query = re.sub(r"```", "", txt)

        return cleaned_query

    @staticmethod
    def json_to_csv(json_data):
        # Convert JSON data to Python list of dictionaries if it's a string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:  # Assume it's already a Python list of dictionaries
            data = json_data

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv", newline=""
        ) as temp_file:
            # Check if data is not empty and is a list
            if data and isinstance(data, list):
                # Extract headers from the first item assuming all items are dictionaries
                headers = data[0].keys()
                # Create a CSV writer object
                csv_writer = csv.DictWriter(temp_file, fieldnames=headers)
                # Write the header
                csv_writer.writeheader()
                # Write the rows
                csv_writer.writerows(data)
                # Store the path for use in the return value
                temp_file_path = temp_file.name
            else:
                # Handle the case where data is empty or not a list
                print("JSON data is empty or not in the expected format.")
                temp_file_path = None

        return temp_file_path

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        """
        Generate SPARQL query, use it to retrieve a response from the gdb and answer
        the question.
        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        prompt = inputs[self.input_key]
        entities = inputs[self.entities_key]

        generated_sparql = self.sparql_generation_select_chain.run(
            {"question": prompt, "entities": entities, "schema": self.graph.get_schema},
            callbacks=callbacks,
        )

        generated_sparql = self.remove_markdown_quotes(generated_sparql)

        _run_manager.on_text("Generated SPARQL:", end="\n", verbose=self.verbose)
        _run_manager.on_text(
            generated_sparql, color="green", end="\n", verbose=self.verbose
        )

        result = self.graph.query(generated_sparql)

        # creating csv temp file inside the _call

        temp_file_path = self.json_to_csv(result)
        print("Saving results to file: ", temp_file_path)

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
                "result": result,  # Include the result as the total token count is within the LLM context window
                "temp_file_path": temp_file_path,  # Add the file path to the results
            }

        return {self.output_key: contextualized_result}
