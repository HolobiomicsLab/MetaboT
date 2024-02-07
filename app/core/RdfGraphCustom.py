from __future__ import annotations

# from rdflib.namespace import RDFS

from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

if TYPE_CHECKING:
    import rdflib

NAMESPACES = {
    "brick": "https://brickschema.org/schema/Brick#",
    "csvw": "http://www.w3.org/ns/csvw#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcam": "http://purl.org/dc/dcam/",
    "doap": "http://usefulinc.com/ns/doap#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "geo": "http://www.opengis.net/ont/geosparql#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "org": "http://www.w3.org/ns/org#",
    "prof": "http://www.w3.org/ns/dx/prof/",
    "prov": "http://www.w3.org/ns/prov#",
    "qb": "http://purl.org/linked-data/cube#",
    "schema": "https://schema.org/",
    "sh": "http://www.w3.org/ns/shacl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "sosa": "http://www.w3.org/ns/sosa/",
    "ssn": "http://www.w3.org/ns/ssn/",
    "time": "http://www.w3.org/2006/time#",
    "vann": "http://purl.org/vocab/vann/",
    "void": "http://rdfs.org/ns/void#",
    "wgs": "https://www.w3.org/2003/01/geo/wgs84_pos#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "enpkg": "https://enpkg.commons-lab.org/kg/",
    "enpkg_module": "https://enpkg.commons-lab.org/module/",
    "ns1": "http://proton.semanticweb.org/protonsys#",
}
PREFIX_STATEMENT = "\n".join(
    f"PREFIX {short}: <{uri}>" for short, uri in NAMESPACES.items()
)

# cls_query_rdf="""
# SELECT DISTINCT ?cls ?com (SAMPLE(?instance) AS ?example)
# WHERE {
#     ?cls a rdfs:Class . 
#     OPTIONAL { ?cls rdfs:comment ?com }
#     OPTIONAL { ?instance a ?cls }
# }
# GROUP BY ?cls ?com

# """

# cls_query_rdf="""

# SELECT DISTINCT ?class ?property ?sampleValue
# WHERE {
#     ?class a rdfs:Class .
# }

# # Use the result of the class query in a UNION with the property query
# UNION

# # Query for properties of instances of each class
# {
#     SELECT DISTINCT ?class ?property (SAMPLE(?value) AS ?sampleValue)
#     WHERE {
#         ?class a rdfs:Class .
#         {
#             SELECT DISTINCT ?instance ?property ?value
#             WHERE {
#                 ?instance a ?class .
#                 ?instance ?property ?value .
#             }
#             LIMIT 100
#         }
#     }
#     GROUP BY ?class ?property
# }
# """

cls_query_rdf = """
SELECT DISTINCT ?cls ?com
WHERE {
    ?cls a rdfs:Class . 
    OPTIONAL { ?cls rdfs:comment ?com }
}
"""

cls_query_rdfs = (
    """SELECT DISTINCT ?cls ?com\n"""
    """WHERE { \n"""
    """    ?instance a/rdfs:subClassOf* ?cls . \n"""
    """    OPTIONAL { ?cls rdfs:comment ?com } \n"""
    """}"""
)


cls_query_owl = (
    """SELECT DISTINCT ?cls ?com\n"""
    """WHERE { \n"""
    """    ?instance a/rdfs:subClassOf* ?cls . \n"""
    """    FILTER (isIRI(?cls)) . \n"""
    """    OPTIONAL { ?cls rdfs:comment ?com } \n"""
    """}"""
)

# ## broad range query for all relationships
# rel_query_rdf = (
#     """SELECT DISTINCT ?rel ?com\n
#     WHERE { \n
#         ?subj ?rel ?obj . \n
#         OPTIONAL { ?rel rdfs:comment ?com } \n
#     }"""
# )

## get more results than the above query : 141 instead of 126 relationships
rel_query_rdf = """
SELECT ?rel ?com
WHERE {
    ?rel a rdf:Property .
    OPTIONAL { ?rel rdfs:comment ?com }
}
"""



rel_query_rdfs = (
    """SELECT DISTINCT ?rel ?com\n"""
    """WHERE { \n"""
    """    ?rel a/rdfs:subPropertyOf* rdf:Property . \n"""
    """    OPTIONAL { ?rel rdfs:comment ?com } \n"""
    """}"""
)


op_query_owl = (
    """SELECT DISTINCT ?op ?com\n"""
    """WHERE { \n"""
    """    ?op a/rdfs:subPropertyOf* owl:ObjectProperty . \n"""
    """    OPTIONAL { ?op rdfs:comment ?com } \n"""
    """}"""
)


dp_query_owl = (
    """SELECT DISTINCT ?dp ?com\n"""
    """WHERE { \n"""
    """    ?dp a/rdfs:subPropertyOf* owl:DatatypeProperty . \n"""
    """    OPTIONAL { ?dp rdfs:comment ?com } \n"""
    """}"""
)

subcls_query_rdf = """
SELECT ?subclass ?superclass
WHERE {
    ?subclass rdfs:subClassOf ?superclass .
    FILTER(?subclass != ?superclass)
}
"""

## TODO : just integrate the needed namespaces in the query

cls_query_rdf = PREFIX_STATEMENT + "\n" + cls_query_rdf
rel_query_rdf = PREFIX_STATEMENT + "\n" + rel_query_rdf
cls_query_rdfs = PREFIX_STATEMENT + "\n" + cls_query_rdfs
rel_query_rdfs = PREFIX_STATEMENT + "\n" + rel_query_rdfs
cls_query_owl = PREFIX_STATEMENT + "\n" + cls_query_owl
op_query_owl = PREFIX_STATEMENT + "\n" + op_query_owl
dp_query_owl = PREFIX_STATEMENT + "\n" + dp_query_owl
subcls_query_rdf = PREFIX_STATEMENT + "\n" + subcls_query_rdf


class RdfGraph:
    """RDFlib wrapper for graph operations.

    Modes:
    * local: Local file - can be queried and changed
    * online: Online file - can only be queried, changes can be stored locally
    * store: Triple store - can be queried and changed if update_endpoint available
    Together with a source file, the serialization should be specified.

    *Security note*: Make sure that the database connection uses credentials
        that are narrowly-scoped to only include necessary permissions.
        Failure to do so may result in data corruption or loss, since the calling
        code may attempt commands that would result in deletion, mutation
        of data if appropriately prompted or reading sensitive data if such
        data is present in the database.
        The best way to guard against such negative outcomes is to (as appropriate)
        limit the permissions granted to the credentials used with this tool.

        See https://python.langchain.com/docs/security for more information.
    """

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

        :param source_file: either a path for a local file or a URL
        :param serialization: serialization of the input
        :param query_endpoint: SPARQL endpoint for queries, read access
        :param update_endpoint: SPARQL endpoint for UPDATE queries, write access
        :param standard: RDF, RDFS, or OWL
        :param local_copy: new local copy for storing changes
        """
        self.source_file = source_file
        self.serialization = serialization
        self.query_endpoint = query_endpoint
        self.update_endpoint = update_endpoint
        self.standard = standard
        self.local_copy = local_copy
        self.prefix_statements = PREFIX_STATEMENT  ## TODO - find and implement a logic of namespaces initialisation (enpkg, enpkg_module, ns1, rdf etc.)
        ## for now, the namespaces are hardcoded in the PREFIX_STATEMENT variable with rdflib namespace prefixing (rdf, rdfs, foaf etc.) + the namespaces from the graph (enpkg, enpkg_module, ns1)

        try:
            import rdflib
            from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
            from rdflib.plugins.stores import sparqlstore
        except ImportError:
            raise ValueError(
                "Could not import rdflib python package. "
                "Please install it with `pip install rdflib`."
            )
        if self.standard not in (supported_standards := ("rdf", "rdfs", "owl")):
            raise ValueError(
                f"Invalid standard. Supported standards are: {supported_standards}."
            )

        if (
            not source_file
            and not query_endpoint
            or source_file
            and (query_endpoint or update_endpoint)
        ):
            raise ValueError(
                "Could not unambiguously initialize the graph wrapper. "
                "Specify either a file (local or online) via the source_file "
                "or a triple store via the endpoints."
            )

        if source_file:
            if source_file.startswith("http"):
                self.mode = "online"
            else:
                self.mode = "local"
                if self.local_copy is None:
                    self.local_copy = self.source_file
            self.graph = rdflib.Graph()
            self.graph.parse(source_file, format=self.serialization)

        if query_endpoint:
            self.mode = "store"
            if not update_endpoint:
                self._store = sparqlstore.SPARQLStore()
                self._store.open(query_endpoint)
            else:
                self._store = sparqlstore.SPARQLUpdateStore()
                self._store.open((query_endpoint, update_endpoint))
            self.graph = rdflib.Graph(self._store, bind_namespaces="none")

            # nspaces = {
            #     "brick": rdflib.Namespace("https://brickschema.org/schema/Brick#"),
            #     "csvw": rdflib.Namespace("http://www.w3.org/ns/csvw#"),
            #     "dc": rdflib.Namespace("http://purl.org/dc/elements/1.1/"),
            #     "dcat": rdflib.Namespace("http://www.w3.org/ns/dcat#"),
            #     "dcmitype": rdflib.Namespace("http://purl.org/dc/dcmitype/"),
            #     "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
            #     "dcam": rdflib.Namespace("http://purl.org/dc/dcam/"),
            #     "doap": rdflib.Namespace("http://usefulinc.com/ns/doap#"),
            #     "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
            #     "geo": rdflib.Namespace("http://www.opengis.net/ont/geosparql#"),
            #     "odrl": rdflib.Namespace("http://www.w3.org/ns/odrl/2/"),
            #     "org": rdflib.Namespace("http://www.w3.org/ns/org#"),
            #     "prof": rdflib.Namespace("http://www.w3.org/ns/dx/prof/"),
            #     "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
            #     "qb": rdflib.Namespace("http://purl.org/linked-data/cube#"),
            #     "schema": rdflib.Namespace("https://schema.org/"),
            #     "sh": rdflib.Namespace("http://www.w3.org/ns/shacl#"),
            #     "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
            #     "sosa": rdflib.Namespace("http://www.w3.org/ns/sosa/"),
            #     "ssn": rdflib.Namespace("http://www.w3.org/ns/ssn/"),
            #     "time": rdflib.Namespace("http://www.w3.org/2006/time#"),
            #     "vann": rdflib.Namespace("http://purl.org/vocab/vann/"),
            #     "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
            #     "wgs": rdflib.Namespace("https://www.w3.org/2003/01/geo/wgs84_pos#"),
            #     "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
            #     "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            #     "rdfs": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
            #     "xsd": rdflib.Namespace("http://www.w3.org/2001/XMLSchema#"),
            #     "xml": rdflib.Namespace("http://www.w3.org/XML/1998/namespace"),
            #     "enpkg": rdflib.Namespace("https://enpkg.commons-lab.org/kg/"),
            #     "enpkg_module": rdflib.Namespace("https://enpkg.commons-lab.org/module/"),
            #     "ns1": rdflib.Namespace("http://proton.semanticweb.org/protonsys#")
            # }

            # for prefix, namespace in nspaces.items():
            #     self.graph.bind(prefix, namespace)

        ## SECTION COMMENTED FOR DEV PURPOSES / FASTER. SHOULD BE DECOMMENTED FOR PRODUCTION
        # Verify that the graph was loaded
        # if not len(self.graph):
        #     raise AssertionError("The graph is empty.")

        ## SECTION COMMENTED FOR INFO PURPOSES, SHOULD NOT BE DECOMMENTED FOR PRODUCTION
        # self.graph.serialize(
        #         destination=self.local_copy, format="turtle"
        #     )

        print("list of namespaces", list(self.graph.namespaces()))
        print("identifier ,", self.graph.identifier)

        # Set schema
        self.schema = ""
        self.load_schema()

    @property
    def get_schema(self) -> str:
        """
        Returns the schema of the graph database.
        """
        return self.schema

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

    def update(
        self,
        query: str,
    ) -> None:
        """
        Update the graph.
        """
        from rdflib.exceptions import ParserError

        try:
            self.graph.update(query)
        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")
        if self.local_copy:
            self.graph.serialize(
                destination=self.local_copy, format=self.local_copy.split(".")[-1]
            )
        else:
            raise ValueError("No target file specified for saving the updated file.")

    @staticmethod
    def _get_local_name(iri: str) -> str:
        if "#" in iri:
            local_name = iri.split("#")[-1]
        elif "/" in iri:
            local_name = iri.split("/")[-1]
        else:
            raise ValueError(f"Unexpected IRI '{iri}', contains neither '#' nor '/'.")
        return local_name

    def _res_to_str(self, res: rdflib.query.ResultRow, var: str) -> str:
        return (
            "<"
            + str(res[var])
            + "> ("
            + self._get_local_name(res[var])
            + ", "
            + str(res["com"])
            + ")"
        )


    def load_schema(self) -> None:
        """
        Load the graph schema information.
        """

        def _rdf_s_schema(
            classes: List[rdflib.query.ResultRow],
            relationships: List[rdflib.query.ResultRow],
            subclasses: List[rdflib.query.ResultRow],
        ) -> str:
            return (
                f"In the following, each IRI is followed by the local name and optionally its description. \n"
                f"The RDF graph supports the following node types:\n"
                f'{", ".join([self._res_to_str(r, "cls") for r in classes])}\n'
                f"The RDF graph supports the following relationships:\n"
                f'{", ".join([self._res_to_str(r, "rel") for r in relationships])}\n'
                f"In the following tuples, each IRI is followed by the superclass"
                f'{", ".join("(<" + r["subclass"] + ">, <" + r["superclass"] + ">)" for r in subclasses)}\n'

            )

        def _format_schema():
            for key, url in NAMESPACES.items():
                self.schema = self.schema.replace(f"<{url}", f"<{key}:")
            return self.schema

        def _add_namespaces_to_schema():
            return (
                f"The namespace prefixes are:\n"
                f'{", ".join([f"{short}: {uri}" for short, uri in NAMESPACES.items()])}\n'
                + self.schema
            )

        if self.standard == "rdf":
            print("query", cls_query_rdf)
            clss = self.query(cls_query_rdf)
            print("query", rel_query_rdf)
            rels = self.query(rel_query_rdf)
            print("query", subcls_query_rdf)
            sub = self.query(subcls_query_rdf)
            self.schema = _rdf_s_schema(clss, rels, sub)
            self.schema = _format_schema()
            self.schema = _add_namespaces_to_schema()

        elif self.standard == "rdfs":
            print("query", cls_query_rdfs)
            clss = self.query(cls_query_rdfs)
            print("query", rel_query_rdfs)
            rels = self.query(rel_query_rdfs)
            self.schema = _rdf_s_schema(clss, rels)
        elif self.standard == "owl":
            clss = self.query(cls_query_owl)
            ops = self.query(op_query_owl)
            dps = self.query(dp_query_owl)
            self.schema = (
                f"The namespace prefixes are:\n"
                f'{", ".join([f"{short}: {uri}" for short, uri in NAMESPACES.items()])}\n'
                f"In the following, each IRI is followed by the local name and "
                f"optionally its description in parentheses. \n"
                f"The OWL graph supports the following node types:\n"
                f'{", ".join([self._res_to_str(r, "cls") for r in clss])}\n'
                f"The OWL graph supports the following object properties, "
                f"i.e., relationships between objects:\n"
                f'{", ".join([self._res_to_str(r, "op") for r in ops])}\n'
                f"The OWL graph supports the following data properties, "
                f"i.e., relationships between objects and literals:\n"
                f'{", ".join([self._res_to_str(r, "dp") for r in dps])}\n'
            )
        else:
            raise ValueError(f"Mode '{self.standard}' is currently not supported.")
