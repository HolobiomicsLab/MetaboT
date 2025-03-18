import logging
import logging.config
import csv
import tempfile
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool
from SPARQLWrapper import JSON, SPARQLWrapper

from ...session import setup_logger, create_user_session
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)

logger = setup_logger(__name__)


class WikidataInput(BaseModel):
    wikidata_id: str = Field(description="A string containing the wikidata id.")

class WikidataStructureSearch(BaseTool):
    name: str = "WIKIDATA_QUERY_TOOL"
    description: str = """
        Takes wikidata id string as input, builds a query, executes it, and returns
        the list of Wikidata IRI's of the compounds present in the input genus.

        Args:
            wikidata_id (str): A string that represents the wikidata id of a taxon.

        Returns:
            str: A string that contains the path to the file with Wikidata IRIs if found, otherwise `None`.
        """
    args_schema = WikidataInput

    ENDPOINT_URL = "https://query.wikidata.org/sparql"
    PREFIXES = """
       PREFIX wd: <http://www.wikidata.org/entity/>
       PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    """
    session_id: str = None

    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id


    def _run(
            self,  wikidata_id: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Optional[str]:

        query = self.build_query(wikidata_id)
        results = self.execute_query(query)
        session_dir = create_user_session(self.session_id, user_session_dir=True)

        if results:
            try:
                bindings = results["results"]["bindings"]
                if bindings:
                    wikidata_ids = [binding["wd_id"]["value"] for binding in bindings]
                    logger.info("Wikidata IDs of annotations found.")
                    # Create a temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=session_dir, mode='w', suffix='.csv', newline='')
                    # Write the results to the temporary file
                    with temp_file as file:
                        writer = csv.writer(file)
                        writer.writerow(['Wikidata ID'])  # Writing headers
                        for wikidata_id in wikidata_ids:
                            writer.writerow([wikidata_id])  # Writing data
                    return temp_file.name

                else:
                    logger.info("No annotations found for the given genus.")
                    return None
            except KeyError:
                logger.error("Unexpected result format.")
                return None
        else:
            return None

    def build_query(self, wikidata_id: str) -> str:
        """
        Constructs a SPARQL query to retrieve Wikidata IDs of annotations based on a wikidata id of the taxa.

        Args:
            wikidata id (str): A string representing the wikidata id  of a taxon.

        Returns:
            str: A SPARQL query targeting the annotations search present in the genus of a given taxon in the given endpoint.
        """
        return f"""
            {self.PREFIXES}     
            SELECT ?wd_id   
            WHERE {{
                 BIND(wd:{wikidata_id} AS ?wd_sp)
                # Ensure the genus is actually a genus (and not a higher clade)
                ?genus wdt:P31 wd:Q16521; # instance of taxon
                wdt:P105 wd:Q34740; # taxonomic rank of genus
                ^wdt:P171* ?wd_sp .
                # Get all child taxa of the genus Tabernaemontana
                ?childtaxa wdt:P171* ?genus.
                ?wd_id wdt:P703 ?childtaxa
           }}
           """

    def execute_query(self, query: str) -> Optional[dict]:
            """
            Sends a SPARQL query to the specified endpoint URL and returns the
            results in JSON format, handling exceptions by logging errors.

            Args:
                query: SPARQL query string.

            Returns:
                dict: Results in JSON format if the query is successful and results are found.
                None: If no results are found or there is an error during the query execution.
            """
            sparql = SPARQLWrapper(self.ENDPOINT_URL)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(600)
            logger.info(f"Executing SPARQL query: {query}")
            try:
                results = sparql.query().convert()
                if not results or (
                        results.get("results") and not results.get("results").get("bindings")
                ):
                    logger.info("Query was successful but no results were found.")
                    return None
                logger.info("Query was successful and results were retrieved.")
                return results
            except Exception as e:
                logger.error(f"An error occurred while querying the endpoint: {e}")
                return None