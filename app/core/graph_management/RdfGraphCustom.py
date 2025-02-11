from __future__ import annotations

import configparser
import csv
import logging.config
import re
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import rdflib
from rdflib import BNode, URIRef
from rdflib.plugins.stores import sparqlstore
from tqdm import tqdm

from app.core.utils import token_counter
from app.core.session import setup_logger

logger = setup_logger(__name__)

parent_dir = Path(__file__).parent.parent.parent
sparql_config_path = parent_dir / "config" / "sparql.ini"


class RdfGraph:
    """
    RdfGraph class handles the RDF graph representing the schema of the endpoint,
    including querying and schema generation. The subjects are rdfs:Class nodes.
    """

    # TODO: handle domain and range of properties rdfs:domain and rdfs:range

    def __init__(
        self,
        query_endpoint: Optional[str],
        standard: Optional[str] = "rdf",
        schema_file: Optional[str] = None,
    ) -> None:
        """
        Set up the RDFlib graph
        Args:
            query_endpoint (Optional[str]): SPARQL endpoint for queries, read access.
            standard (Optional[str]): RDF, RDFS, or OWL.
            schema_file (Optional[str]): File containing the RDF graph schema, in turtle format.
        Raises:
            ValueError: If the standard is not one of rdf, rdfs, or owl
            ValueError: If no query endpoint is provided
        """
        self.query_endpoint = query_endpoint
        self.standard = standard
        self.schema_file = schema_file
        self.namespaces = None
        self.config = self.load_config(sparql_config_path)
        logger.info("sparql_config_path %s", sparql_config_path)
        self.CLS_RDF = self.config.get("sparqlQueries", "CLS_RDF")
        self.CLS_REL_RDF = self.config.get("sparqlQueries", "CLS_REL_RDF")
        self.EXCLUDED_URIS = self.config.get("excludedURIs", "uris").split(",")

        try:
            if self.standard not in (supported_standards := ("rdf", "rdfs", "owl")):
                raise ValueError(
                    f"Invalid standard. Supported standards are: {supported_standards}."
                )
            if not query_endpoint:
                raise ValueError("No query endpoint provided.")
        except ValueError as e:
            logger.error(f"Error: {e}")
            raise

        self._store = sparqlstore.SPARQLStore()
        self._store.open(query_endpoint)
        self.graph = rdflib.Graph(self._store, bind_namespaces="none")
        self.load_schema()

    @staticmethod
    def load_config(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        return config

    @property
    def get_schema(self) -> str:
        return self.schema

    def get_prop_and_val_types(self, class_uri: str) -> List[Tuple[str, str]]:
        """
        Retrieves and filters properties and their value types for a specified class URI. It excludes properties with alphanumeric sequences, post-underscore and certain URIs.

        Args:
            class_uri (str): The URI of the class for which to retrieve property and value types.
        Returns:
            List[Tuple[str, str]]: A list of tuples, each containing the property URI and the value type.
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

    def get_graph_from_classes(self, classes: List[Dict]) -> rdflib.graph.Graph:
        """
        Generates an RDF graph from a list of class URIs, that represents the types of triples that were found in the endpoint.
        Each triple has a class as a subject, property as predicate, and one possible value type of that property as object.

        :example:
            `ns1:InChIkey ns1:has_npc_pathway ns1:ChemicalTaxonomy .`
            `ns1:LCMSAnalysisPos ns1:has_massive_license <Untyped> .`

        Args:
            classes (List[Dict]): A list of dictionaries, each representing a class and its details.
        Returns:
            rdflib.graph.Graph: An RDF graph object.
        """
        graph = rdflib.Graph()

        for cl in tqdm(classes, desc="Adding classes to graph"):
            class_ref = URIRef(cl.get("cls"))
            properties_and_values = self.get_prop_and_val_types(cl.get("cls"))
            for property_uri, sample_value in properties_and_values:
                value_ref = (
                    BNode() if sample_value == "Untyped" else URIRef(sample_value)
                )
                graph.add((class_ref, URIRef(property_uri), value_ref))
        return graph

    def query(
        self,
        query: str,
    ) -> List[csv.DictReader]:
        """
        queries a graph using a SPARQL statement and returns the results as a list of
        dictionaries.

        Args:
          query (str): a string that represents a SPARQL query to be executed on the graph data.

        Returns:
            List[csv.DictReader]: a list of dictionaries containing the results of the query.
        """
        from rdflib.exceptions import ParserError
        from rdflib.query import ResultRow

        try:
            res = self.graph.query(query_object=query, initNs={}, initBindings={})

        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")

        except Exception as e:
            raise ValueError(f"An error occurred while querying the graph: {e}")

        # TODO [Franck]: deal with other possible exceptions (timeout, etc)

        csv_str = res.serialize(format="csv").decode("utf-8")
        return list(csv.DictReader(StringIO(csv_str)))

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

    def _res_to_str(self, res: dict, namespaces: List[Tuple[str, str]]) -> str:
        """
        Formats a string representing information about a class, its local name (e.g. text after last "/" in URI),
        its associated label and comment. The class URI is given with namespace notation.

        Args:
         res (Dict): A dictionary with response data, containing specific keys.
         namespaces (List[Tuple[str, str]]): A list of tuples for namespace resolution.

        Returns:
            str: A formatted string using `res`, and `namespaces`, structured as `<formatted_var> (local_name, res['label'], res['com'])`.

        Example:
            `ns1:LFpair (LFpair, A LF pair, A pair of 2 LCMSFeature)`
            `ns1:ChemicalTaxonomy (ChemicalTaxonomy, None, None)`
        """

        formatted_var = self._replace_uri_by_prefix(str(res["cls"]), namespaces)
        local_name = self._get_local_name(res["cls"])

        return f"<{formatted_var}> ({local_name}, {res.get('label', '')}, {res.get('com', '')})"

    def get_namespaces(self) -> List[Tuple[str, str]]:
        """
        Returns:
          A list of tuples where each tuple contains two strings representing namespaces (prefix, uri).
        """
        if self.namespaces is None:
            raise ValueError("No namespaces found.")
        return self.namespaces

    def load_schema(self) -> None:
        """
        loads graph schema information based on the specified standard (rdf,
        rdfs, owl) into the `schema` attribute.
        """

        def _rdf_s_schema(
            classes: List[Dict],
            graph: rdflib.graph.Graph,
        ) -> str:
            schema = graph.serialize(format="turtle")
            self.namespaces = list(graph.namespaces())

            formatted_namespaces = [
                (prefix, str(uri)) for prefix, uri in self.namespaces
            ]
            logger.info("namespaces %s", formatted_namespaces)

            return (
                f"The namespace prefixes are: {formatted_namespaces}\n"
                + f"In the following, each URI is followed by the local name and optionally its rdfs:Label, and optionally its rdfs:comment. \n"
                + f"The RDF graph supports the following node types:\n"
                + f'{", ".join([self._res_to_str(row, formatted_namespaces) for row in classes])}\n'
                + f"The RDF graph have the following schema:\n"
                + f"{schema} \n"
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

                logger.info("number of tokens %s", token_counter(self.schema))

            elif self.standard == "rdfs":
                # TODO : implement the rdfs schema
                pass
            elif self.standard == "owl":
                # TODO : implement the owl schema
                pass
            else:
                raise ValueError(f"Mode '{self.standard}' is currently not supported.")
