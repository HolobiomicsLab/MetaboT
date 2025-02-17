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
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.utils import token_counter
from app.core.session import setup_logger, create_user_session
from app.core.memory.database_manager import tools_database

from typing import Optional

# new imports for similarity search
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


logger = setup_logger(__name__)


SPARQL_GENERATION_SELECT_TEMPLATE = """ Task: Generate a SPARQL SELECT statement for querying a graph database.
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

Precision: The query must include only necessary prefixes related to the question and conditions as specified. It should be ready to run in a SPARQL endpoint without requiring any additional editing or formatting. 

Include only necessary variables that are directly referenced in the query. Do not define or select unused variables.

Exclusivity: Do not encapsulate the query in any form of quotes (single, double, or block quotes). The response must contain the SPARQL query and nothing else.

Prefix Usage: Only include prefixes that are actually used in the query. Do not include unused and unnecessary prefixes. For example, if the foaf prefix is not used in the query, it should not be included.

Schema and Property Alignment: Ensure SPARQL query strictly adheres to the defined schema. Use only properties and node types that are explicitly provided in the schema. Use properties with nodes that are directly associated with them in the schema. Do not misapply properties between similar but distinct node types, such as ?InChIkey and ?InChIkey2D.

Object Validation: Ensure the objects used in the query are valid for the given properties and classes according to the schema. Verify that the class-property-object relationships are correctly followed as defined in the schema. Do not mix objects between different classes for the same property.
For example, here is the correct usage of objects: 
```
?chemicalEntity ns1:has_wd_id ?wd_id .
?chemicalEntity ns1:has_smiles ?smiles .
```
And here is the incorrect usage properties with objects (does not follow the schema):
```
?chemicalEntity ns1:has_wd_id ?InChIkey .
```
In this example, ns1:has_wd_id should not link ?chemicalEntity to ?InChIkey because ns1:has_wd_id only links ?chemicalEntity to ?wd_id(Wikidata ID of Chemical entity). 

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
If the question asks for features, ensure that LCMSFeatureList is accessed through LCMSAnalysis and not directly through LabExtract.

Entities: Use the IRI provided by the additional information to construct the query, if there is any. When available, choose to use the IRI rather than the Literal value of the entity.
Double check that provided entities are not used as subjects in the query. For example neither a Wikidata IRI (e.g., <http://www.wikidata.org/entity/Q15435584>) should never appear as a subject. 

Simplification: Produce a query that is as concise as possible. Do not generate triples not necessary to answer the question.

Casting: Given the schemas, when filtering values for properties, directly use the literal values without unnecessary casting to xsd:string, since they are already expected to be strings according to the RDF schema provided.

Validation: Before finalizing your response, ensure the query is syntactically correct and follows the SPARQL standards, verify that all selected variables are referenced in the WHERE clause or are used in the output. 
Double check that it uses properties as defined in the schema and does not have any unused prefixes. It should be capable of being executed in a compatible SPARQL endpoint without errors.

Be careful with the similar but not the same properties such as: 
-ns1:has_lcms_feature_list and -ns1:has_lcms_feature which link to different objects.

Also, double check that the properties of the following classes are not interchanged, since these are similar but not the same:
-LabExtract vs. LabObject vs.RawMaterial
-ChemicalEntity vs. ChEMBLChemical
-InChIkey vs. InChIkey2D
-LCMSFeature vs. LCMSFeatureList
-ChEMBLChemical vs. ChEMBLAssay
For example, make sure that the property of ChEMBLChemical is not used together with ChEMBLAssay if ChEMBLAssay does not have that property.
Important Note: Ensure that you correctly follow the property relationships as defined in the schema. For example, do not place properties with classes that do not directly own them. Here are correct examples of the property use:
ex:John a ex:Person ;
   ex:hasName "John Doe" ;
   ex:authorOf ex:SomeBook .
ex:SomeBook a ex:Book ;
     ex:hasTitle  "Some Book Title" .

This example demonstrates incorrect use of properties:
ex:SomeBook a ex:Book ;
    ex:hasName "Some Book Title" .
Thus, avoid using properties with the classes and objects that are not associated with them.
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


SPARQL_IMPROVEMENT_TEMPLATE = """Task: Review and Refine SPARQL Query. You are provided with the incorrect SPARQL query which should be refined based on the schema of the knowledge graph. 
Here are list of steps that would help you to accomplish your task:

1.Verify Subjects: For each subject in the query, identify its class in the schema.

2.Check Subjects, Properties and Objects: For each subject-property-object triple:
For each property identify where this property is located in the schema. 
Confirm that the property is valid for the subject's class according to the schema. 
Be careful with the similar but not the same properties such as: 
-ns1:has_lcms_feature_list and -ns1:has_lcms_feature which link to different objects.
Ensure the object is of the correct class or datatype as specified in the schema and can be used in the triple.
Also, double check that the properties of the following classes are not interchanged, since these are similar but not the same:
-LabExtract vs. LabObject vs.RawMaterial
-ChemicalEntity vs. ChEMBLChemical
-InChIkey2D vs. InChIkey
-LCMSFeature vs. LCMSFeatureList
-ChEMBLChemical vs. ChEMBLAssay

3. Identify and Correct Errors: If any properties or objects do not match the schema, rewrite the SPARQL query to correctly reflect the schema's structure.

4. Validate Query Entities and Roles:
Ensure correct property-object alignment: Verify that properties use the appropriate entities as objects. For instance:
If ns1:has_wd_id is used, the object must be a Wikidata IRI.
If ns2:target_id is used, the object must be a ChEMBLTarget IRI.
Avoid using these properties with objects that do not match the expected entity type.
Restrict entities to proper roles: Double-check that the specified entities are not misused as subjects in the query. For example:
A Wikidata IRI must not be used as a subject; it should only be used as an object. Similarly, a ChEMBLTarget IRI must not appear as a subject.

Schema interpretation check:
If you cannot identify any errors in the query, this indicates a potential misinterpretation of the schema. Carefully review the schema documentation again. Ensure every property and entity usage adheres to the defined structure and constraints.

5. If the template query is provided, consider it as an example of a right SPARQL query, compare the incorrect SPARQL query with it and identify the errors in the incorrect SPARQL query.

If you could not find errors in the query, it means that you misread the schema. Please, review the schema carefully again and do all the steps again, you need to identify the mistake and provide the refined query.

6. Validation: Before finalizing your response, ensure the query is syntactically correct and follows the SPARQL standards, verify that all selected variables are referenced in the WHERE clause or are used in the output.
Include only necessary variables that are directly referenced in the query. Do not define or select unused variables.

7. Output Format: Your response should consist solely of the corrected SPARQL query that is fully compliant with the schema. Do not include any markdown syntax (e.g., triple backticks), preamble words (like "sparql"), or any other text outside the SPARQL query itself.

SPARQL query for you to correct:
{generated_sparql}

The schema is:
{schema}

Additional entities:
{entities}

Example of right SPARQL query:
{template_query}
"""

SPARQL_IMPROVEMENT_PROMPT = PromptTemplate(
    input_variables=["generated_sparql", "schema", "entities", "template_query"],
    template=SPARQL_IMPROVEMENT_TEMPLATE,
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
    sparql_improvement_chain: LLMChain = None
    requires_params = True
    graph: RdfGraph = None
    session_id: str = None

    def __init__(self, llm: dict, graph: RdfGraph, session_id: str, **kwargs):
        super().__init__(**kwargs)
        try:
            self.sparql_generation_select_chain = LLMChain(
                llm=llm["llm_o"],
                prompt=SPARQL_GENERATION_SELECT_PROMPT,
                # verbose=True,  #### FOR debugging
            )
            self.sparql_improvement_chain = LLMChain(
                llm=llm["llm_o3_mini"],
                prompt=SPARQL_IMPROVEMENT_PROMPT,
            )
        except KeyError as e:
            logger.error(f"Missing LLM key: {e}")
            raise
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
        #Check if the result is empty
        if not result:
            print("The query result is empty.")
            #retrieving the schema nodes related to the initial query
            schema_retrieved = self.search_nodes(generated_sparql)
            #retrieving the sparql query template
            template_query = self.find_similar_query(generated_sparql)
            # Regenerate the SPARQL query
            regenerated_sparql = self.sparql_improvement_chain.run(
                {
                    "generated_sparql": generated_sparql,
                    "schema": schema_retrieved,
                    "entities": entities,
                    "template_query": template_query,
                }
            )

            regenerated_sparql = self.remove_markdown_quotes(regenerated_sparql)
            regenerated_sparql = self.remove_xsd_prefix(regenerated_sparql)

            logger.info("Regenerated SPARQL query: %s", regenerated_sparql)

            # Query the graph again with the regenerated SPARQL query
            result = self.graph.query(regenerated_sparql)


        # Create csv temp file inside the _call
        temp_file_path = self.json_to_csv(result)

        # Add check conditions (if temp_file_path=null->generate new sparql query)
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
        filtered_lines = [line for line in lines if not (line.startswith("PREFIX xsd:") or line.startswith("PREFIX foaf:"))]
        updated_query = "\n".join(filtered_lines)
        return updated_query

    def search_nodes(self, query):
        """
        Searches for related nodes in the FAISS database using a query.

        Args:
            query (str): The search query to find related nodes.

        Returns:
            list: A list of related nodes found in the database.
        """
        current_dir = os.path.dirname(__file__)

        # Construct the path to the faiss_db directory
        db_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'data', 'faiss_db'))

        embeddings = OpenAIEmbeddings()
        db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        related_nodes = db.similarity_search(query, 12)
        return related_nodes

    def find_similar_query(self, input_query):
        """
            Finds the most similar query from the database to the input query.

            Args:
                input_query (str): The query to find similar queries for.

            Returns:
                dict: The most similar query from the database and its similarity score.
            """
        # Get the directory of the current script
        current_dir = os.path.dirname(__file__)

        # Construct the path to the queries.json file
        json_file = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'data', 'queries.json'))

        # Extract the query texts
        database_queries = self.load_queries(json_file)
        query_texts = [entry['query'] for entry in database_queries]

        # Combine the input query with the database query texts
        all_queries = [input_query] + query_texts

        # Vectorize the queries using TF-IDF
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(all_queries)

        # Compute cosine similarity between the input query and all other queries
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Find the index of the most similar query
        most_similar_index = np.argmax(cosine_similarities)

        # Retrieve the most similar query from the database
        most_similar_query = database_queries[most_similar_index]
        similarity_score = cosine_similarities[most_similar_index]

        return most_similar_query

    def load_queries(self, json_file):
        """
            Loads queries from a JSON file.

            Args:
                json_file (str): The path to the JSON file containing the queries.

            Returns:
                list: A list of queries loaded from the JSON file.
            """
        with open(json_file, 'r') as file:
            data = json.load(file)
            return data['queries']


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

            output_data = {
                "output": {
                    "paths": [str(temp_file_path)],
                }
            }

            logger.info(f"Output data: {output_data}")

            db_manager = tools_database()
            try:
                db_manager.put(data=json.dumps(output_data), tool_name="tool_sparql")
            except Exception as e:
                logger.error(f"Error saving to database: {e}")

        else:
            # Handle the case where data is empty or not a list
            logger.info("JSON data is empty or not in the expected format.")
            temp_file_path = None

        return temp_file_path
