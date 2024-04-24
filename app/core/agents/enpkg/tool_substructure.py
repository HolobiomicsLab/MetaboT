import logging
import logging.config
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool
from SPARQLWrapper import JSON, SPARQLWrapper

from app.core.utils import setup_logger

from ..tool_interface import ToolTemplate

logger = setup_logger(__name__)

"""
Class in test phase

1) It should provide wikidata ids of substructures of a given SMILES string

2) Then the enpkg agent gives theses ids to the Sparql agent

3) The sparql agent should 'understand', regarding the context of the question, the wikidata ids provided and the turtle schema file, 
that the user is asking for the substructures of the molecule.

4) The sparql query should be something like this:

    PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?ik2d ?smiles
    WHERE {
        ?extract rdf:type enpkg:LabExtract .
        FILTER(regex(str(?extract), "VGF152_B02")) # Tabernaemontana coffeoides seeds extract
        ?extract enpkg:has_LCMS ?lcms .
        ?lcms enpkg:has_lcms_feature_list ?feature_list .
        ?feature_list enpkg:has_lcms_feature ?feature .
        ?feature enpkg:has_sirius_annotation|enpkg:has_isdb_annotation ?annotation .
        ?annotation enpkg:has_InChIkey2D ?ik2d .
        ?ik2d enpkg:has_smiles ?smiles .
        ?ik2d enpkg:is_InChIkey2D_of ?ik .
        ?ik enpkg:has_wd_id ?wd_id .
        VALUES ?wd_id { <id1> <id2> ... } # Use retrieved IDs here            <------------------- HERE
    }

    The VALUES clause filters the results to only include the substructures of the molecule.
"""


class SmileSubstructureResolver(ToolTemplate):
    ENDPOINT_URL = "https://idsm.elixir-czech.cz/sparql/endpoint/idsm"
    PREFIXES = """
        PREFIX sachem: <http://bioinfo.uochb.cas.cz/rdf/v1.0/sachem#>
        PREFIX idsm: <https://idsm.elixir-czech.cz/sparql/endpoint/>
    """

    def __init__(self):
        super().__init__()

    @tool("SMILES_SUBSTRUCTURE_RESOLVER")
    def tool_func(self, smiles: str) -> Optional[List[str]]:
        """
        Find the substructure Wikidata IDs of a given SMILES string.

        Args:
            smiles (str): A string containing the SMILES representation of a molecule.

        Returns:
            List[str]: List of Wikidata IDs of the substructures of the molecule, if found.
        """
        query = self.build_query(smiles)
        results = self.execute_query(query)

        if results:
            try:
                bindings = results["results"]["bindings"]
                if bindings:
                    wikidata_ids = [binding["wd_id"]["value"] for binding in bindings]
                    logger.info("Substructure Wikidata IDs found.")
                    return wikidata_ids
                else:
                    logger.info("No substructures found for the given SMILES string.")
                    return None
            except KeyError:
                logger.error("Unexpected result format.")
                return None
        else:
            return None

    def build_query(self, smiles: str) -> str:
        """
        Constructs a SPARQL query to retrieve Wikidata IDs based on a molecule's SMILES string.

        Args:
            smiles (str): A string representing the SMILES of a molecule.

        Returns:
            str: A SPARQL query targeting the substructure search in the given endpoint.
        """
        return f"""
            {self.PREFIXES}
            SELECT ?wd_id
            WHERE {{
                VALUES ?SUBSTRUCTURE {{ "{smiles}" }}
                ?wd_id sachem:substructureSearch _:b16.
                _:b16 sachem:query ?SUBSTRUCTURE.
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
