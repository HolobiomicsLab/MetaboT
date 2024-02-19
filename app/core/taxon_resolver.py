import logging
from SPARQLWrapper import SPARQLWrapper, JSON

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TaxonResolver:
    ENDPOINT_URL = 'https://query.wikidata.org/sparql'
    PREFIXES = """
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX pr: <http://www.wikidata.org/prop/reference/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
    """

    def build_query(self, taxon_name):
        return f"""
            {self.PREFIXES}
            SELECT *
            WHERE
            {{
              ?wikidata wdt:P225 "{taxon_name}" .
            }}
        """

    def execute_query(self, query):
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
       