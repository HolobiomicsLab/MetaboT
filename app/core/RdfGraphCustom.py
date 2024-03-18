from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING, Dict
import re
import rdflib
from rdflib import URIRef, Namespace, Literal, BNode
from rdflib.plugins.stores import sparqlstore
from tqdm import tqdm
import tiktoken
import logging
import csv
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RdfGraph:
    """
    RdfGraph class handles the RDF graph database, including querying and schema generation. Graph must having defined rdfs:Class nodes.
    """
    
    # sparql query to get all classes and their comments / faster than CLS_EX_RDF
    #TODO: handle domain and range of properties rdfs:domain and rdfs:range
    CLS_RDF = """
    SELECT DISTINCT ?cls ?com ?label
        WHERE {
            ?cls a rdfs:Class . 
            OPTIONAL { ?cls rdfs:comment ?com }
            OPTIONAL { ?cls rdfs:label ?label }
        }
        GROUP BY ?cls ?com ?label
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
        # "http://www.w3.org/2000/01/rdf-schema#label",
        "http://www.w3.org/2000/01/rdf-schema#comment",
        "http://www.w3.org/2000/01/rdf-schema#Class",
        "http://xmlns.com/foaf/0.1/depiction",
    ]

    def __init__(
        self,
        query_endpoint: Optional[str],
        standard: Optional[str] = "rdf",
        schema_file: Optional[str] = None,
    ) -> None:
        """
        Set up the RDFlib graph
        :param query_endpoint: SPARQL endpoint for queries, read access
        :param standard: RDF, RDFS, or OWL
        :param schema_file: File containing the RDF graph schema, in turtle format.
        """
        self.query_endpoint = query_endpoint
        self.standard = standard
        self.schema_file = schema_file
        self.namespaces = None
        if self.standard not in (supported_standards := ("rdf", "rdfs", "owl")):
            raise ValueError(
                f"Invalid standard. Supported standards are: {supported_standards}."
            )
        if not query_endpoint:
            raise ValueError("No query endpoint provided.")
            
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

    def get_prop_and_val_types(self, class_uri: str) -> List[Tuple[str, str]]:
        """
        Retrieves and filters properties and their value types for a specified class URI. It excludes properties with alphanumeric sequences post-underscore and certain URIs.

        :param class_uri: The URI of the class for which to retrieve property and value types.
        :type class_uri: str
        :return: A list of tuples, each containing the property URI and the value type.
        """
        query = self.CLS_REL_RDF.format(class_uri=class_uri)
        results = self.query(query)

        filtered_results = [
            (str(r.get("property")), str(r.get("valueType")))
            for r in results
            if not re.search(r"_([0-9a-fA-F]+)$", str(r.get("property")))
            and str(r.get("property")) not in self.EXCLUDED_URIS
        ]

        return filtered_results

    def get_graph_from_classes(
        self, classes: List[Dict]
    ) -> rdflib.graph.Graph:
        """
        Generates an RDF graph from a list of class triplets, with each class as a subject and its properties and values as predicates and objects.

        :param classes: A list of `rdflib.query.ResultRow` objects, each representing a class and its details.
        :type classes: List[rdflib.query.ResultRow]
        :return: An `rdflib.graph.Graph` object.
        """

        graph = rdflib.Graph()
        
        for cl in tqdm(classes, desc="Adding classes to graph"):
            class_ref = URIRef(cl.get("cls"))
            properties_and_values = self.get_prop_and_val_types(cl.get("cls"))
            for property_uri, sample_value in properties_and_values:
                value_ref = BNode() if sample_value == "Untyped" else URIRef(sample_value)
                graph.add((class_ref, URIRef(property_uri), value_ref))
        return graph

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
            res = self.graph.query(query_object=query, initNs={})

        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")
        
        csv_str = res.serialize(format="csv").decode("utf-8")
        return list(csv.DictReader(StringIO(csv_str)))

    @staticmethod
    def token_counter(text: str) -> int:

        tokenizer = tiktoken.encoding_for_model(model_name="gpt-4")
        tokens = tokenizer.encode(text)
        return len(tokens)

    @staticmethod
    def _get_local_name(iri: str) -> str:
        for sep in ["#", "/"]:
            prefix, found, local_name = iri.rpartition(sep)
            if found:
                return local_name
        raise ValueError(f"Unexpected IRI '{iri}', contains neither '#' nor '/'.")

    @staticmethod
    def _replace_uri_by_prefix(text, namespaces):
        if text is None:
            return text
        for key, url in namespaces:
            text = text.replace(url, f"{key}:")
        return text

    def _res_to_str(self, res, namespaces) -> str:
        """
        Formats a string based on a response dictionary, a specific variable, and namespaces.

        :param res: A dictionary with response data, containing specific keys.
        :param var: A string key to extract a value from `res`.
        :param namespaces: A list of tuples for namespace resolution.
        :return: A formatted string using `res`, `var`, and `namespaces`, structured as `<formatted_var> (local_name, res['com'], formatted_example)`.
        """

        formatted_var = self._replace_uri_by_prefix(str(res['cls']), namespaces)
        local_name = self._get_local_name(res['cls'])
        return f"<{formatted_var}> ({local_name}, {res.get('label', '')}, {res.get('com', '')})"
    
    def get_namespaces(self) -> List[Tuple[str, str]]:
        if self.namespaces is None:
            raise ValueError("No namespaces found.")
        return self.namespaces

    def load_schema(self) -> None:
        """
        Load the graph schema information into the `schema` attribute depending on the standard.
        """

        def _rdf_s_schema(
            classes: List[Dict],
            graph: rdflib.graph.Graph,
        ) -> str:
            schema = graph.serialize(format="turtle")
            self.namespaces = list(graph.namespaces())
            formatted_namespaces = [(prefix, str(uri)) for prefix, uri in self.namespaces]
            logging.info("namespaces %s", formatted_namespaces)
            return (
                f"The namespace prefixes are: {formatted_namespaces}\n"
                + f"In the following, each URI is followed by the local name and optionally its rdfs:Label, and optionally its rdfs:comment. \n"
                + f"The RDF graph supports the following node types:\n"
                + f'{", ".join([self._res_to_str(row, formatted_namespaces) for row in classes])}\n'
                + f"The RDF graph have the following schema:\n" + f"{schema} \n"
            )

        if self.schema_file:
            with open(self.schema_file, "r") as f:
                self.schema = f.read()
                
        else:
            if self.standard == "rdf":
                logging.info("query %s", self.CLS_RDF)
                clss = self.query(self.CLS_RDF)
                graph = self.get_graph_from_classes(clss)
                self.schema = _rdf_s_schema(clss, graph)
                logging.info("number of tokens %s", self.token_counter(self.schema))

            elif self.standard == "rdfs":
                ## TODO : implement the rdfs schema
                pass
            elif self.standard == "owl":
                ## TODO : implement the owl schema
                pass
            else:
                raise ValueError(f"Mode '{self.standard}' is currently not supported.")
