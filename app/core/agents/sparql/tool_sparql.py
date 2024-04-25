from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from typing import Dict

from langchain.chains.llm import LLMChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.utils import setup_logger

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


logger = setup_logger(__name__)


SPARQL_GENERATION_SELECT_TEMPLATE = """Task: Generate a SPARQL SELECT statement for querying a graph database.
For instance, to find all email addresses of John Doe, the following query in backticks would be suitable:

```
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?email
WHERE {{
    ?person foaf:name "John Doe" .
    ?person foaf:mbox ?email .
}}
```

Please generate a SPARQL query based on the following requirements. The output must strictly adhere to these guidelines:

Output Format: Your response should consist solely of the SPARQL query. Ensure the query is fully executable without any modifications or removals necessary. Do not include any markdown syntax (e.g., triple backticks), preamble words (like "sparql"), or any other text outside the SPARQL query itself.

Content Clarity: The query should be clearly structured and formatted for readability. Use appropriate SPARQL conventions, prefixes, and syntax.

Precision: The query must include all necessary prefixes and conditions as specified. It should be ready to run in a SPARQL endpoint without requiring any additional editing or formatting.

Exclusivity: Do not encapsulate the query in any form of quotes (single, double, or block quotes). The response must contain the SPARQL query and nothing else. Any non-query text will be considered an error and will need correction.

Contextualization : Use only the node types and properties provided in the schema. Do not use any node types and properties that are not explicitly provided. Include all necessary prefixes.

Entities : Use the URI provided by the additional information to construct the query, if there is any. When available, use the URI rather than the Literal value of the entity.

Simplification: Produce a query that is as concise as possible. Do not generate triples not necessary to answer the question.

Casting: Given the schemas, when filtering values for properties, directly use the literal values without unnecessary casting to xsd:string, since they are already expected to be strings according to the RDF schema provided.

Validation: Before finalizing your response, ensure the query is syntactically correct and follows the SPARQL standards. It should be capable of being executed in a compatible SPARQL endpoint without errors.

Schema:
{schema}

Additional information:
{entities}

The question is:
{question}

"""


SPARQL_GENERATION_SELECT_PROMPT = PromptTemplate(
    input_variables=["schema", "entities", "question"],
    template=SPARQL_GENERATION_SELECT_TEMPLATE,
)


class SparqlInput(BaseModel):
    question: str = Field(description="the original question from the user")
    entities: str = Field(
        description="strings containing for all entities, entity name and the corresponding entity identifier"
    )


##Question-answering against an RDF or OWL graph by generating SPARQL statements.
class GraphSparqlQAChain(BaseTool):
    name = "SPARQL_QUERY_RUNNER"
    description = """
    The agent resolve the user's question by querying the knowledge graph database. 
    The two inputs should be a string containing the user's question and a string containing the resolved entities in the question.

        Args:
            question (str): the original question from the user.
            entities (str): strings containing for all entities, entity name, the class and the corresponding entity identifier.

        Returns:
          dict: A dictionary containing the contextualized sparql result.
        
        Example:
            question: "What is the capital of France?"
            entities: "France has the DBPEDIA IRI http://dbpedia.org/resource/France; capital has the DBPEDIA http://dbpedia.org/ontology/capital"
            tool._run(question, entities)

        """
    verbose: bool = True
    args_schema = SparqlInput
    sparql_generation_select_chain: LLMChain = None
    graph: RdfGraph = None

    def __init__(self, llm: LLMChain, graph: RdfGraph, **kwargs):
        super().__init__(**kwargs)
        self.sparql_generation_select_chain = LLMChain(
            llm=llm,
            prompt=SPARQL_GENERATION_SELECT_PROMPT,
            # verbose=True   #### FOR debugging
        )
        self.graph = graph

    def _run(
        self,
        question: str,
        entities: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, str]:

        logger.info(
            "providing question and entities to the chain for generating SPARQL query"
        )
        logger.info("question: %s", question)
        logger.info("Entities: %s", entities)

        generated_sparql = self.sparql_generation_select_chain.run(
            {
                "question": question,
                "entities": entities,
                "schema": self.graph.get_schema,
            }
        )

        generated_sparql = self.remove_markdown_quotes(generated_sparql)
        generated_sparql = self.remove_xsd_prefix(generated_sparql)

        logger.info("Generated SPARQL query: %s", generated_sparql)

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
        tokens_question = RdfGraph.token_counter(question)
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

        return {"result": contextualized_result}

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
        lines = query.split("\n")
        filtered_lines = [line for line in lines if not line.startswith("PREFIX xsd:")]
        updated_query = "\n".join(filtered_lines)
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
            os.makedirs(
                kgbot_temp_dir, exist_ok=True
            )  # Make the directory if it doesn't exist

            # Define the path for the new CSV file within the "kgbot" directory
            temp_csv_path = os.path.join(
                kgbot_temp_dir, tempfile.mktemp(suffix=".csv", dir=kgbot_temp_dir)
            )

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
