from typing import Optional

from SPARQLWrapper import JSON, SPARQLWrapper


from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


from app.core.utils import setup_logger


logger = setup_logger(__name__)


class TaxonInput(BaseModel):
    taxon_name: str = Field(description="A string containing the taxon name.")


class TaxonResolver(BaseTool):
    name: str = "TAXON_RESOLVER"
    description: str = """
    Takes a taxon name string as input, builds a query, executes it, and returns
    the Wikidata IRI if found.

    Args:
        taxon_name (str): A string that represents the name of a taxon.

    Returns:
        str: A string that contains the Wikidata IRI if found, otherwise `None`.
    """
    args_schema = TaxonInput
    ENDPOINT_URL = "https://query.wikidata.org/sparql"
    PREFIXES = """
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX pr: <http://www.wikidata.org/prop/reference/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
    """
    openai_key: str = None

    def __init__(self, openai_key: str = None):
        super().__init__()
        self.openai_key = openai_key

    def _run(
        self, taxon_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Optional[str]:

        query = self.build_query(taxon_name)
        results = self.execute_query(query)

        if results:
            try:
                bindings = results["results"]["bindings"]

                if bindings:  # Check if the list is not empty
                    res = "wikidata IRI is " + bindings[0]["wikidata"]["value"]
                    logger.info("Results found for the given taxon name. {res}")
                    return res
                else:
                    logger.info("No results found for the given taxon name.")
                    return None
            except KeyError:
                logger.error("Unexpected result format.")
                return None
        else:
            return None

    def build_query(self, taxon_name: str) -> str:
        """
        Constructs a SPARQL query to retrieve information about a taxon based on
        its name.

        Args:
          taxon_name (str): a string representing the name of a taxon.

        Returns:
          str : Sparql query that target the P225 taxon wikidata id.
        """
        return f"""
            {self.PREFIXES}
            SELECT *
            WHERE
            {{
              ?wikidata wdt:P225 "{taxon_name}" .
            }}
        """

    def execute_query(self, query: str) -> Optional[dict]:
        """
        Sends a SPARQL query to a specified endpoint URL and returns the
        results in JSON format, handling exceptions by logging errors.

        Args:
            query: Sparql query string.

        Returns:
            dict: Results in JSON format if the query is successful and results are found.
            None: If no results are found, it logs an info message and returns `None`. If there
            is an unexpected result format or an error during the process, it logs an error.
        """
        sparql = SPARQLWrapper(self.ENDPOINT_URL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(600)
        logger.info(f"Executing query to wikidata sparql API: {query}")
        try:
            results = sparql.queryAndConvert()
            # check if results are empty, result dict is empty or bindings are empty
            if not results or (
                results.get("results") and not results.get("results").get("bindings")
            ):
                logger.info("Query was successful but no results were found.")
                return None
            logger.info("Query was successful.")
            return results
        except Exception as e:
            logger.error(f"An error occurred while querying wikidata: {e}")
            return None
