from __future__ import annotations

# from rdflib.namespace import RDFS

from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
)
import re

if TYPE_CHECKING:
    import rdflib

from typing import List, Optional, Tuple
import re
import rdflib
from rdflib import URIRef, Namespace, Literal
from rdflib.plugins.stores import sparqlstore
from tqdm import tqdm
import tiktoken

    
    
class RdfGraph:
    CLS_RDF = """
    SELECT DISTINCT ?cls ?com (SAMPLE(?instance) AS ?example)
    WHERE {
        ?cls a rdfs:Class . 
        OPTIONAL { ?cls rdfs:comment ?com }
        OPTIONAL { ?instance a ?cls }
    }
    GROUP BY ?cls ?com
    """
    
    CLS_REL_RDF = """
    SELECT ?property (SAMPLE(COALESCE(?type, STR(DATATYPE(?value)), "Untyped")) AS ?valueType) WHERE {{
        {{
        SELECT ?instance WHERE {{
            ?instance a <{class_uri}> .
        }} LIMIT 1000
        }}
        ?instance ?property ?value .
        OPTIONAL {{
        ?value a ?type .
        }}
    }}
    GROUP BY ?property ?type
    LIMIT 300
    """
    
    EXCLUDED_URIS = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://www.w3.org/2000/01/rdf-schema#comment",
        "http://www.w3.org/2000/01/rdf-schema#Class",
        "http://xmlns.com/foaf/0.1/depiction"
    ]
    

    def __init__(
        self,
        source_file: Optional[str] = None,
        serialization: Optional[str] = "ttl",
        query_endpoint: Optional[str] = None,
        update_endpoint: Optional[str] = None,
        standard: Optional[str] = "rdf",
        local_copy: Optional[str] = None,
    ) -> None:
        """
        Set up the RDFlib graph
        :param query_endpoint: SPARQL endpoint for queries, read access
        :param standard: RDF, RDFS, or OWL
        """
        self.source_file = source_file
        self.serialization = serialization
        self.query_endpoint = query_endpoint
        self.update_endpoint = update_endpoint
        self.standard = standard
        self.local_copy = local_copy
        if self.standard not in (supported_standards := ("rdf", "rdfs", "owl")):
            raise ValueError(
                f"Invalid standard. Supported standards are: {supported_standards}."
            )

        if query_endpoint:
            self._store = sparqlstore.SPARQLStore()
            self._store.open(query_endpoint)
            self.graph = rdflib.Graph(self._store, bind_namespaces="none")

        self.load_schema()

    @property
    def get_schema(self) -> str:
        """
        Returns the schema of the graph database.
        """
        return self.schema

    def get_prop_and_val_types(self, class_uri: str) -> List[Tuple[str, str, str]]:
        
        template = self.CLS_REL_RDF   
        query = template.format(class_uri=class_uri)
        res = self.query(query)
        res = [(str(r["property"]), str(r["valueType"])) for r in res]
        excluded_uris = [
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://www.w3.org/2000/01/rdf-schema#label",
            "http://www.w3.org/2000/01/rdf-schema#comment",
            "http://www.w3.org/2000/01/rdf-schema#Class",
            "http://xmlns.com/foaf/0.1/depiction"
        ]
        # Filter out properties with alphanumeric (hexadecimal) sequences after an underscore
        filtered_results = []
        for property_uri, value_type in res:
            # Regex to match properties that do NOT have a hexadecimal sequence after an underscore
            if not re.search(r'_([0-9a-fA-F]+)', property_uri) and property_uri not in excluded_uris:
                filtered_results.append((property_uri, value_type))
                
        return filtered_results
    
    def get_graph_from_triplet(self, classes: List[rdflib.query.ResultRow]) -> rdflib.graph.Graph:
        g = rdflib.Graph()

        for cl in tqdm(classes, desc="Adding classes to graph"):
            class_ref = URIRef(str(cl["cls"]))
            properties_and_values = self.get_prop_and_val_types(str(cl["cls"]))
            for property_uri, sample_value in properties_and_values:
                property_ref = URIRef(property_uri)
                sample_value_ref = URIRef(sample_value)
                g.add((class_ref, property_ref, sample_value_ref))
                
        return g


    def query(
        self,
        query: str,
    ) -> List[rdflib.query.ResultRow]:
        """
        Query the graph.
        """
        from rdflib.exceptions import ParserError
        from rdflib.query import ResultRow

        try:
            res = self.graph.query(query_object=query)

        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")
        return [r for r in res if isinstance(r, ResultRow)]
    
    
    @staticmethod
    def token_counter(text: str) -> int:

        tokenizer = tiktoken.encoding_for_model(model_name='gpt-4')
        tokens = tokenizer.encode(text)
        return len(tokens)

    @staticmethod
    def _get_local_name(iri: str) -> str:
        for sep in ['#', '/']:
            prefix, found, local_name = iri.rpartition(sep)
            if found:
                return local_name
        raise ValueError(f"Unexpected IRI '{iri}', contains neither '#' nor '/'.")

    @staticmethod
    def _format_text(text, namespaces):
        if text is None:
            return text
        for key, url in namespaces:
            text = text.replace(url, f"{key}:")
        return text

    def _res_to_str(self, res, var, namespaces) -> str:
        formatted_var = self._format_text(str(res[var]), namespaces)
        local_name = self._get_local_name(res[var])
        formatted_example = self._format_text(str(res["example"]), namespaces)
        return f"<{formatted_var}> ({local_name}, {res['com']}, {formatted_example})"


    def load_schema(self) -> None:
        """
        Load the graph schema information.
        """

        def _rdf_s_schema(
            classes: List[rdflib.query.ResultRow],
            graph: rdflib.graph.Graph,
            
        ) -> str:
            schema = graph.serialize(format='turtle')
            namespaces = list(graph.namespaces())
            return (
                f"In the following, each IRI is followed by the local name and optionally its description and optionally an example. \n" + \
                f"The RDF graph supports the following node types:\n" + \
                f'{", ".join([self._res_to_str(r, "cls", namespaces) for r in classes])}\n'
                f"The RDF graph have the following schema:\n" + \
                f"{schema} \n" 
            )


        if self.standard == "rdf":
            print("query", self.CLS_RDF)
            clss = self.query(self.CLS_RDF)
            graph = self.get_graph_from_triplet(clss)
            self.schema = _rdf_s_schema(clss, graph)
            print('number of tokens', self.token_counter(self.schema))

        elif self.standard == "rdfs":
            ## TODO : implement the rdfs schema
            pass
        elif self.standard == "owl":
            ## TODO : implement the owl schema
            pass
        else:
            raise ValueError(f"Mode '{self.standard}' is currently not supported.")
