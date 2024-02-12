from tools_script import SparqlTool, DBRetriever, SimpleAgent, SimpleTool
from prompts import (
    chemical_class_template,
    taxon_agent_template,
    target_prompt_template,
    structure_agent_template,
    unit_template,
)
from langchain.agents import Tool
import json


def make_taxon_tool(endpoint_url):
    """
    Creates a taxonomic lookup tool that queries a SPARQL endpoint to retrieve information about taxa.

    This function sets up a SPARQL query for retrieving detailed information about biological extracts
    related to a given taxon from a knowledge graph. It also formats the results into a dictionary
    for easy interpretation. The tool is then encapsulated within a `SimpleAgent` which can be used
    to process natural language inputs and return structured taxon information.
    """

    # Set the SPARQL query template for retrieving taxon information
    taxon_template = """
    PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX enpkgmodule: <https://enpkg.commons-lab.org/module/>
    select * where {{ 
        ?extract rdf:type enpkg:LabExtract .
        ?process enpkg:has_lab_process ?extract ; 
                enpkg:submitted_taxon '{taxon}' ;
                enpkgmodule:has_broad_organe ?broad_organe ;
                enpkgmodule:has_organe ?organe ;
                enpkgmodule:has_subsystem ?subsystem ;
                enpkgmodule:has_tissue ?tissue ;
    }} 
    """

    # Set the tool name and description for the TaxonLookup tool
    taxon_tool_name = "TaxonLookup"
    taxon_tool_desc = """Use tool when need to get extract ID for a species or taxon. 
                        Input should be taxon name.
                        Returns dictionary of possible extract URIs for the taxon of interest with other information."""

    # Function to format the output data from the SPARQL query
    def taxon_format(output):
        if not output:
            return (
                "No taxons were found. Either the specific taxon doesn't exist in the knowledge graph, "
                "or the question is asking about all taxons. Either way, tell the agent to proceed."
            )
        return {
            item["extract"]["value"]: {
                "Type": "https://enpkg.commons-lab.org/kg/LabExtract",
                **{
                    key: value["value"].rsplit("/", 1)[-1]
                    for key, value in item.items()
                    if key != "extract"
                },
            }
            for item in output
        }

    taxon_tool = SparqlTool(
        endpoint_url,
        taxon_tool_name,
        taxon_tool_desc,
        prompt_template=taxon_template,
        result_formatter=taxon_format,
    ).make_tool()

    taxon_agent_desc = "Use when you need to know the uri for a taxon. Return best extract URI in the context of the question"
    taxon_agent = SimpleAgent(
        taxon_agent_template,
        "TaxonTool",
        taxon_agent_desc,
        [taxon_tool],
        parser="keyword_question",
        model="gpt-4",
    )
    return taxon_agent.make_tool()


def make_runsparql_tool(endpoint_url):
    """
    Creates a tool to run SPARQL queries against a specified endpoint.

    This method sets up a SparqlTool with a given endpoint URL, which can be used
    to execute SPARQL queries. The tool is useful for situations where keywords
    have been extracted, and identifiers have been found, and a SPARQL query needs
    to be executed to retrieve further information.
    """
    tool_name = "SparqlQueryRunner"
    tool_desc = "Useful to run Sparql queries after keywords have been extracted and identifiers have been found."

    run_sparql_query = SparqlTool(endpoint_url, tool_name, tool_desc)
    return run_sparql_query.make_tool()


def make_chemicalclass_tool(local_files_dir, ClassDB=None):
    """
    Creates a tool to retrieve URIs for chemical classes from a local file.

    This function sets up a DBRetriever tool to parse a local JSON file containing
    chemical class information and to provide a searchable interface. It can load
    pre-existing ChromaDB embeddings if provided, or generate new embeddings if not.
    The tool is then used to return URIs for chemical classes mentioned in user queries.

    """
    class_tool_desc = (
        "Use to retrieve URIs for chemical classes mentioned in the question."
    )
    class_tool_name = "ClassTool"
    class_filepath = f"{local_files_dir}local_files/npc_classes.json"

    def find_noids_word(s):
        return next(
            (
                word.lower()
                for word in s.split("_")
                if "noids" in word or "loids" in word
            ),
            s.lower(),
        )

    def class_parser(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)

        return sorted(
            (
                x["class"]["value"].split("https://enpkg.commons-lab.org/kg/", 1)[-1]
                for x in data["results"]["bindings"]
            ),
            key=find_noids_word,
        )

    NPCClass = DBRetriever(
        chemical_class_template,
        class_filepath,
        class_tool_name,
        class_tool_desc,
        class_parser,
    )

    NPCClass.load_embeddings(ClassDB) if ClassDB else NPCClass.prepare_data()

    NPCClass.set_retriever(docs=6)

    return NPCClass.make_tool()


def make_target_tool():
    """
    Creates a tool to format the target name for SPARQL query use.

    This function initializes a SimpleAgent with a specific prompt template
    designed to format target names correctly for SPARQL queries. It's particularly
    useful when you need to ensure the target names are in a format that the SPARQL
    endpoint will recognize and process correctly.

    """
    target_agent_name = "TargetTool"
    target_agent_desc = (
        "Use to get the correct string for the target name to use in SPARQL query"
    )

    target_agent = SimpleAgent(
        target_prompt_template,
        target_agent_name,
        target_agent_desc,
        [],
        model="gpt-3.5-turbo",
    )
    return target_agent.make_tool()


def make_structure_tool():
    """
    Creates a tool to format SPARQL subqueries for retrieving chemical structures.

    It's intended for use when a SPARQL subquery needs to be generated to
    retrieve structural information about a chemical, based on its SMILES representation.
    """
    structure_agent_name = "StructureTool"
    structure_agent_desc = (
        "Use when you need to get the sparql subquery to retrieve structures."
    )

    # The SimpleAgent and structure_agent_template need to be defined elsewhere in the code.
    structure_agent_template = """
    PREFIX idsm: <https://idsm.elixir-czech.cz/sparql/endpoint/>
    PREFIX sachem: <http://bioinfo.uochb.cas.cz/rdf/v1.0/sachem#>

    ?ik a enpkg:InChIkey;
        enpkg:has_wd_id ?wd_id .
        SERVICE idsm:wikidata {{
            VALUES ?SUBSTRUCTURE {{"{input}"}} 
            ?wd_id sachem:substructureSearch _:b16.
            _:b16 sachem:query ?SUBSTRUCTURE.
        }}
    """

    def format_structure_template(smiles):
        return structure_agent_template.format(input=smiles)

    format_structure_tool = Tool(
        name="StructureQueryTool",
        description="Format the structure SPARQL template",
        func=format_structure_template,
    )

    # Instantiate the SimpleAgent with the template and tool
    structure_agent = SimpleAgent(
        structure_agent_template,
        structure_agent_name,
        structure_agent_desc,
        [format_structure_tool],
    )

    return structure_agent.make_tool()


def make_unit_tool(local_files_dir, UnitDB=None):
    """
    Creates a tool to retrieve units from a local JSON file.

    This function initializes a DBRetriever with a specific template for units.
    It's used when a question mentions a numerical measure and a corresponding unit
    needs to be retrieved. The tool can either load pre-existing embeddings from UnitDB
    or compute new embeddings if UnitDB is not provided.
    """

    unit_tool_name = "UnitTool"
    unit_tool_desc = "Use to retrieve units if question mentions a numerical measure."
    unit_filepath = f"{local_files_dir}local_files/ENPKG_units.json"

    def unit_parser(filepath):
        with open(filepath, "r") as f:
            return json.load(f)

    unit_agent = DBRetriever(
        unit_template, unit_filepath, unit_tool_name, unit_tool_desc, parser=unit_parser
    )

    # Load precomputed embeddings if provided, otherwise compute them.
    unit_agent.load_embeddings(UnitDB) if UnitDB else unit_agent.prepare_data()

    # Set the retriever with the appropriate number of documents to retrieve.
    unit_agent.set_retriever(docs=1)

    return unit_agent.make_tool()


def make_schemaretriever_tool(local_files_dir):
    """
    Creates a tool to retrieve the schema of a knowledge graph from a local TTL file.

    This tool reads the entire contents of a TTL (Turtle) file that represents the schema
    of a knowledge graph. It is used to obtain all triples of the knowledge graph schema
    which can be useful for LLM to understand the structure and relationships within the graph.

    """
    schema_retriever_name = "SchemaRetrieverTool"
    schema_retriever_desc = "Useful to get all triples of knowledge graph schema"
    schema_filepath = f"{local_files_dir}local_files/merged.ttl"

    def retriever_schema(_):
        with open(schema_filepath, "r") as file:
            return file.read()

    schema_retriever_tool = SimpleTool(
        schema_retriever_name, schema_retriever_desc, retriever_schema
    )
    return schema_retriever_tool.make_tool()


def make_commonerrors_tool():
    """
    Creates a tool that provides common fixes for errors in SPARQL queries.

    This function generates a static tool that, when called, returns a list of
    common errors and their fixes. It is particularly useful when a SPARQL query
    has returned no results, and the user needs guidance on how to self-correct the query.

    """
    errors_name = "CommonErrorsTool"
    errors_desc = "Useful if sparql query returned no results to self-correct"

    def common_errors(_):
        return (
            "Here are some fixes to common errors. Check that the query you tried doesn't make any of them "
            "and try the RunSparqlQuery tool again with a new query.\n\n"
            "1. If using feature make sure you access it with this: {?lcms enpkg:has_lcms_feature_list/enpkg:has_lcms_feature ?feature}\n"
            "2. URI with prefix should NOT be in quotation marks (don't do this - 'enpkg:npc_Saponaceolide_triterpenoids')"
        )

    errors_tool = SimpleTool(errors_name, errors_desc, common_errors)
    return errors_tool.make_tool()


def make_toolset(endpoint_url, local_files_dir="./", ClassDB=None, UnitDB=None):
    """
    Main function to build all tools for KGAI, specific to ENPKG.

    Args:
        endpoint_url (str): SPARQL endpoint.
        local_files_dir (str): path to directory containing 'local_files/' directory, ending with '/'.
        ClassDB (VectorDB, optional): Preloaded VectorDB of chemical class info.
        UnitDB (VectorDB, optional): Preloaded VectorDB of unit info.

    Returns:
        list: A list of all the tools created.
    """
    tools = [
        make_runsparql_tool(endpoint_url),
        make_taxon_tool(endpoint_url),
        make_chemicalclass_tool(local_files_dir, ClassDB),
        make_target_tool(),
        make_structure_tool(),
        make_unit_tool(local_files_dir, UnitDB),
        make_schemaretriever_tool(local_files_dir),
        make_commonerrors_tool(),
    ]

    return tools
