from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from typing import Dict
from pathlib import Path

from langchain.chains.llm import LLMChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.utils import setup_logger, token_counter, create_user_session

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


logger = setup_logger(__name__)


SPARQL_GENERATION_SELECT_TEMPLATE = """
Task: Generate a SPARQL SELECT statement for querying a graph database.
For instance, to find all email addresses of John Doe, the following query in backticks is suitable:
```
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?email
WHERE {{
    ?person foaf:name "John Doe" .
    ?person foaf:mbox ?email .
}}
```
Your task is to generate a SPARQL query based on the following requirements. The output must strictly adhere to these guidelines, please, read them carefully:

Output Format: Your response should consist solely of the SPARQL query. Do not include any markdown syntax (e.g., triple backticks), preamble words (like "sparql"), or any other text outside the SPARQL query itself.

Content Clarity: Ensure the query is clear, readable, properly formatted and includes only the necessary prefixes that are used in the query.

Precision: The query must include only necessary prefixes related to the question and conditions as specified. It should be ready to run in a SPARQL endpoint without requiring any additional editing or formatting. Do not include any prefixes that are not used in the query.

Exclusivity: Do not encapsulate the query in any form of quotes (single, double, or block quotes). The response must contain the SPARQL query and nothing else.

Prefix Usage: Only include prefixes that are actually used in the query. Do not include unused and unnecessary prefixes. For example, if the foaf prefix is not used in the query, it should not be included.

Schema and Property Alignment: Ensure SPARQL query strictly adheres to the defined schema. Use only properties and node types that are explicitly provided in the schema. Use properties with nodes that are directly associated with them in the schema. Do not misapply properties between similar but distinct node types, such as ?InChIkey and ?InChIkey2D.

Object Validation: Ensure the objects used in the query are valid for the given properties and classes according to the schema. Verify that the class-property-object relationships are correctly followed as defined in the schema. Do not mix objects between different classes for the same property.

Path Traversal: If you need to access properties that do not directly belong to a given class, first link the class to an associated class that has the desired properties. This ensures the query adheres to the schema constraints.

For example, to access the CHEMBL_ID of an entity represented by ?InChIkey2D, you need to first link ?InChIkey2D to its associated chemical entity, and then access the CHEMBL_ID through the chemical entity, since ?InChIkey2D does not have the property ns2:has_chembl_id directly. The SPARQL query should contain the following:
```
?InChIkey2D ns1:is_InChIkey2D_of ?chemicalEntity .
?chemicalEntity ns2:has_chembl_id ?chembl_id.
```
If the question asks for annotations, access the annotations through the feature in the feature list. For instance, to get the ISDB annotations of a particular lab extract, the SPARQL query should contain:
```
?labExtract ns1:has_LCMS ?analysis .
?analysis ns1:has_lcms_feature_list ?feature_list .
?feature_list ns1:has_lcms_feature ?feature .
?feature ns1:has_isdb_annotation ?Annotation .
```
Entities: Use the IRI provided by the additional information to construct the query, if there is any. When available, choose to use the IRI rather than the Literal value of the entity.

Simplification: Produce a query that is as concise as possible. Do not generate triples not necessary to answer the question.

Casting: Given the schemas, when filtering values for properties, directly use the literal values without unnecessary casting to xsd:string, since they are already expected to be strings according to the RDF schema provided.

Validation: Before finalizing your response, ensure the query is syntactically correct and follows the SPARQL standards. Double check that it uses properties as defined in the schema and does not have any unused prefixes. It should be capable of being executed in a compatible SPARQL endpoint without errors.

Important Note: Ensure that you correctly follow the property relationships as defined in the schema. For example, do not place properties with classes that do not directly own them. Here are correct examples of the property use:
ex:John a ex:Person ;
   ex:hasName "John Doe" ;
   ex:authorOf ex:SomeBook .
ex:SomeBook a ex:Book ;
     ex:hasTitle  "Some Book Title" .

And this example demonstrates incorrect use of properties:
ex:SomeBook a ex:Book ;
    ex:hasName "Some Book Title" .
Thus, avoid using properties with the classes that are not associated with them.
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
            entities: "France has the DBPEDIA IRI http://dbpedia.org/resource/France; capital has the DBPEDIA IRI http://dbpedia.org/ontology/capital"
            tool._run(question, entities)

        """
    verbose: bool = True
    args_schema = SparqlInput
    sparql_generation_select_chain: LLMChain = None
    graph: RdfGraph = None
    session_id: str = None

    def __init__(self, llm: LLMChain, graph: RdfGraph, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.sparql_generation_select_chain = LLMChain(
            llm=llm,
            prompt=SPARQL_GENERATION_SELECT_PROMPT,
            # verbose=True,  #### FOR debugging
        )
        self.graph = graph
        self.session_id = session_id

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

        temp_file_path = self.json_to_csv(self, result)

        logger.info("Saving results to file: %s", temp_file_path)

        # Convert the SPARQL query output to  a string if it's not already

        if isinstance(result, dict):  # Assuming result2 is a dictionary (JSON)
            result2_string = json.dumps(result)
        else:
            result2_string = str(
                result
            )  # Make sure it's a string if it's not a dictionary

        # Now call the token_counter method with the string count the tokens
        tokens_result = token_counter(result2_string)
        tokens_question = token_counter(question)
        tokens_query = token_counter(generated_sparql)

        # Sum of tokens from different parts
        total_tokens = tokens_result + tokens_question + tokens_query

        # Define the LLM context window size
        llm_context_window = 6000

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
    def json_to_csv(self, json_data):
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
            # Getting the temporary directory path
            
            session_dir = create_user_session(self.session_id, user_session_dir=True)

            # Create a NamedTemporaryFile within the session directory and keep it after closing
            with tempfile.NamedTemporaryFile(suffix=".csv", dir=session_dir, delete=False) as temp_file:
                temp_csv_path = Path(temp_file.name)  # Convert the temp file path to a Path object

                # Open the temp file path again for writing CSV data
                with temp_csv_path.open(mode="w", newline="") as file:
                    # Extract headers from the first item, assuming all items are dictionaries
                    headers = data[0].keys()
                    # Create a CSV writer object
                    csv_writer = csv.DictWriter(file, fieldnames=headers)
                    # Write the header
                    csv_writer.writeheader()
                    # Write the rows
                    csv_writer.writerows(data)

            temp_file_path = temp_csv_path

        else:
            # Handle the case where data is empty or not a list
            logger.info("JSON data is empty or not in the expected format.")
            temp_file_path = None

        return temp_file_path