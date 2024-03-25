import logging
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# The `TaxonResolver` class constructs and executes SPARQL queries to retrieve Wikidata IRIs
# based on taxon names.
class TaxonResolver:
    ENDPOINT_URL = 'https://query.wikidata.org/sparql'
    PREFIXES = """
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX pr: <http://www.wikidata.org/prop/reference/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
    """

    def build_query(self, taxon_name : str) -> str:
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

    def execute_query(self, query : str) -> Union[dict, None]:
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
            try:
                    results = sparql.queryAndConvert()
                    return results
            except Exception as e:
                    logging.error(f"An error occurred while querying wikidata: {e}")
                    return None

    def query_wikidata(self, taxon_name : str) -> str:
        """
        Takes a taxon name as input, builds a query, executes it, and returns
        the Wikidata IRI if found.
        
        Args:
          taxon_name (str): A string that represents the name of a taxon.
        
        Returns:
            str: A string that contains the Wikidata IRI if found, otherwise `None`.
        """
        query = self.build_query(taxon_name)
        results = self.execute_query(query)
        
        if results:
            try:
                bindings = results["results"]["bindings"]
                if bindings:  # Check if the list is not empty
                    return "wikidata IRI is " + bindings[0]['wikidata']['value']
                else:
                    logging.info("No results found for the given taxon name.")
                    return None
            except KeyError:
                logging.error("Unexpected result format.")
                return None
        else:
            return None
       