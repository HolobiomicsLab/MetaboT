from SPARQLWrapper import SPARQLWrapper, JSON

class TaxonResolver:
    ENDPOINT_URL = 'https://query.wikidata.org/sparql'
    PREFIXES = """
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX pr: <http://www.wikidata.org/prop/reference/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
    """

    def __init__(self):
        pass  # No need to initialize anything specific now

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
            print(f"An error occurred: {e}")
            return None

    def query_wikidata(self, taxon_name : str):
        query = self.build_query(taxon_name)
        results = self.execute_query(query)
        if results:
            try:
                return "wikidata IRI is "+[result['wikidata']['value'] for result in results["results"]["bindings"]][0]
            except KeyError:
                print("Unexpected result format")
                return None
        else:
            return None
