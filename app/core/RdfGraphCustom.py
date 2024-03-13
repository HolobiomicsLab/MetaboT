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

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class RdfGraph:
    """
    RdfGraph class handles the RDF graph representing the schema of the endpoint, 
    including querying and schema generation. The subjects are rdfs:Class nodes.
    """

    # sparql query to get all classes and their comments / faster than CLS_EX_RDF
    # TODO: handle domain and range of properties rdfs:domain and rdfs:range
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
                f"Invalid standard. Supported standards are: {
                    supported_standards}."
            )
        if not query_endpoint:
            raise ValueError("No query endpoint provided.")
            # TODO [Franck]: instead of this test, query_endpoint chould simply not be optional (?)

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
        Retrieves and filters properties and their value types for a specified class URI. It excludes properties with alphanumeric sequences, post-underscore and certain URIs.

        :param class_uri: The URI of the class for which to retrieve property and value types.
        :type class_uri: str
        :return: A list of tuples, each containing the property URI "property" and the value type "valueType".
        """
        query = self.CLS_REL_RDF.format(class_uri=class_uri)
        results = self.query(query)

        filtered_results = [
            (str(r.get("property")), str(r.get("valueType")))
            for r in results
            # TODO [Franck]: why filter out "_"?
            if not re.search(r"_([0-9a-fA-F]+)$", str(r.get("property")))
            and str(r.get("property")) not in self.EXCLUDED_URIS
        ]

        return filtered_results

    def get_graph_from_classes(
        self,
        classes: List[Dict]
    ) -> rdflib.graph.Graph:
        """
        Generates an RDF graph from a list of class URIs, that represents the types of triples that were found in the endpoint.
        Each triple has a class as a subject, property as predicate, and one possible value type of that property as object.

        :example: 
            `ns1:InChIkey ns1:has_npc_pathway ns1:ChemicalTaxonomy .`
            `ns1:LCMSAnalysisPos ns1:has_massive_license <Untyped> .`

        :param classes: A list of `rdflib.query.ResultRow` objects, each representing a class and its details.
        :type classes: List[rdflib.query.ResultRow]
        :return: An `rdflib.graph.Graph` object.
        """

        graph = rdflib.Graph()
        for cl in tqdm(classes, desc="Adding classes to graph"):
            class_ref = URIRef(cl.get("cls"))
            properties_and_values = self.get_prop_and_val_types(cl.get("cls"))
            for property_uri, value_type in properties_and_values:
                value_ref = BNode() if value_type == "Untyped" else URIRef(value_type)
                # Add the triple class property value_type
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
        # TODO [Franck]: deal with other possible exceptions (timeout, etc)

        csv_str = res.serialize(format="csv").decode("utf-8")
        return list(csv.DictReader(StringIO(csv_str)))

    @staticmethod
    def token_counter(text: str) -> int:
        tokenizer = tiktoken.encoding_for_model(model_name="gpt-4")
        # TODO [Franck]: the model name should be a config param
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
        Formats a string representing information about a class, its associated label and comment.
        The class URI is given with namespace notation.

        :example:
            `ns1:LFpair (LFpair, A pair of 2 LCMSFeature)`
            `ns1:ChemicalTaxonomy (ChemicalTaxonomy, None)`

        :param res: A dictionary with response data, containing keys 'cls' (class URI), 'label' (rdfs:label), and 'com' (rdfs:comment)
        :param namespaces: A list of tuples for namespace resolution.
        :return: A string formatted as `<class URI> (local_name, res['label'], res['com'])`.
        """
        formatted_var = self._replace_uri_by_prefix(
            str(res['cls']), namespaces)
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
            formatted_namespaces = [(prefix, str(uri))
                                    for prefix, uri in self.namespaces]
            logging.info("namespaces %s", formatted_namespaces)
            return (
                f"The namespace prefixes are: {formatted_namespaces}\n"
                + f"In the following, each URI is followed by the local name and optionally its rdfs:Label, and optionally its rdfs:comment. \n"
                + f"The RDF graph supports the following node types:\n"
                + f'{", ".join([self._res_to_str(row, formatted_namespaces)
                               for row in classes])}\n'
                + f"The RDF graph has the following schema:\n" +
                f"{schema} \n"
            )

        if self.schema_file:
            # Load schema from an existing file (typically an ontology)
            with open(self.schema_file, "r") as f:
                self.schema = f.read()
        else:
            # Extract the schema from the endpoint
            if self.standard == "rdf":
                logging.info("query %s", self.CLS_RDF)

                # Get the list of classes to analyze
                clss = self.query(self.CLS_RDF)

                # For each class, find the properties that their instances may have, as well as the object types
                graph = self.get_graph_from_classes(clss)
                self.schema = _rdf_s_schema(clss, graph)
                logging.info("number of tokens %s",
                             self.token_counter(self.schema))

            elif self.standard == "rdfs":
                # TODO : implement the rdfs schema
                pass
            elif self.standard == "owl":
                # TODO : implement the owl schema
                pass
            else:
                raise ValueError(
                    f"Mode '{self.standard}' is currently not supported.")
