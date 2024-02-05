from drafts.originals.tools_script_original import RunSparql, QueryTool, nested_value, DBRetriever, SimpleAgent, SimpleTool
from prompts import chemical_class_template, taxon_agent_template, target_prompt_template, structure_agent_template, unit_template
from langchain.agents import Tool
import json


def make_taxon_tool(endpoint_url):
    
    
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
    taxon_tool_name = 'TaxonLookup'
    taxon_tool_desc = """Use tool when need to get extract ID for a species or taxon. 
                        Input should be taxon name.
                        Returns dictionary of possible extract URIs for the taxon of interest with other information."""

    # Define a function to format the output data from the SPARQL query
    def taxon_format(output):
        formatted_data = {}
        for item in output:
            entity_id = item['extract']['value']
            formatted_data[entity_id] = {x: item[x]['value'].split('/')[-1] for x in item if x != 'extract'}
            formatted_data[entity_id]['Type'] = 'https://enpkg.commons-lab.org/kg/LabExtract'

        if formatted_data == {}:
            return "No taxons were found. Either the specific taxon doesn't exist in the knowledge graph or the question is asking about all taxons. Either way tell the agent to precede."
        return formatted_data

    # Create an instance of the QueryTool class for the TaxonLookup tool
    taxon_class = QueryTool(taxon_template, taxon_tool_desc, taxon_tool_name, endpoint_url, taxon_format)
    taxon_class.make_tool()

    # Create the TaxonTool using the specified template, list of tools (in this case only TaxonLookup), and name
    taxon_agent_desc = 'Use when you need to know the uri for a taxon. Return best extract URI in the context of the question'
    taxon_agent = SimpleAgent(taxon_agent_template, 'TaxonTool', taxon_agent_desc, [taxon_class.tool], parser = 'keyword_question', model = 'gpt-4')
    taxon_agent.make_tool()
    return taxon_agent

def make_runsparql_tool(endpoint_url):
    tool_name = "SparqlQueryRunner"
    tool_desc = "Useful to run Sparql queries after keywords have been extracted and identifiers have been found."

    # Create an instance of the RunSparql class
    run_sparql_query = RunSparql(endpoint_url, tool_name, tool_desc)
    run_sparql_query.make_tool()

    return run_sparql_query

def make_chemicalclass_tool(local_files_dir, ClassDB=None):
    # Sorting function
    def find_noids_word(s):
        words = s.split('_')
        for word in words:
            if "noids" in word or "loids" in word:
                return word.lower()
        return s.lower()

    # Define a function to parse a file containing JSON data and extract values from nested keys
    def class_parser(filepath):
        # Open the file and load the JSON data
        with open(filepath, 'r') as f:
            data = json.load(f)

        def remove_prefix(uri, prefix='https://enpkg.commons-lab.org/kg/'):
            return uri.split(prefix, 1)[-1]
        
        # Extract the values from the nested keys 'class' and 'value'
        class_list = [remove_prefix(nested_value(x, ['class', 'value'])) for x in data['results']['bindings']]
        class_list.sort(key=find_noids_word)
        return class_list 

    # Set the description and name for the class tool
    class_tool_desc = 'Use to retrieve URIs for chemical classes mentioned in the question.'
    class_tool_name = 'ClassTool'
    class_filepath = local_files_dir + 'local_files/npc_classes.json'

    # Create an instance of the db_class using the provided parameters
    NPCClass = DBRetriever(chemical_class_template, class_filepath, class_tool_name, class_tool_desc, class_parser)

    if ClassDB:
        NPCClass.load_embeddings(ClassDB)
    else:
        NPCClass.get_embeddings()

    NPCClass.make_tool(docs=6)
    return NPCClass

def make_target_tool():
    target_agent_name = 'TargetTool'
    target_agent_desc = 'Use to get the correct string for the target name to use in SPARQL query'

    target_agent = SimpleAgent(target_prompt_template, target_agent_name, target_agent_desc, [], model='gpt-3.5-turbo')
    target_agent.make_tool()
    return target_agent

def make_structure_tool():
    # Set the SPARQL query template for subquering structures
    structure_template = """
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


    # Create sparql template format tool
    def format_structure_template(smiles):
        return structure_template.format(input=smiles)

    format_structure_tool = Tool(name='StructureQueryTool',
                                description= 'Format the structure sparql template',
                                func = format_structure_template)

    

    # Create the StructureTool using the specified template, list of tools (in this case only StructureQueryTool), and name
    structure_agent_name = 'StructureTool'
    structure_agent_desc = 'Use when you need to get the sparql subquery to retrieve structures.'
    
    structure_agent = SimpleAgent(structure_agent_template, structure_agent_name, structure_agent_desc, [format_structure_tool])
    structure_agent.make_tool()
    return structure_agent

def make_unit_tool(local_files_dir, UnitDB=None):
    # Define a function to parse a file containing JSON data
    def unit_parser(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data

    # Set the description and name for the unit tool
    unit_tool_desc = 'Use to retrieve units if question mentions a numerical measure.'
    unit_tool_name = 'UnitTool'

    # Set the filepath of the JSON file containing the unit data
    unit_filepath = local_files_dir + 'local_files/ENPKG_units.json'

    # Create an instance of the db_class using the provided parameters
    unit_agent = DBRetriever(unit_template, unit_filepath, unit_tool_name, unit_tool_desc, unit_parser)

    if UnitDB:
        unit_agent.load_embeddings(UnitDB)
    else:
        unit_agent.get_embeddings()
    unit_agent.make_tool(docs=1)
    return unit_agent

def make_schemaretriever_tool(local_files_dir):
    def retriever_schema(null_arg):
        with open(local_files_dir + 'local_files/merged.ttl', 'r') as file:
            ttl_schema = file.read()
        return ttl_schema
    
    schema_retriever_name = 'SchemaRetrieverTool'
    schema_retriever_desc = 'Useful to get all triples of knowledge graph schema'

    schema_retriever_tool = SimpleTool(schema_retriever_name, schema_retriever_desc, retriever_schema)
    schema_retriever_tool.make_tool()
    return schema_retriever_tool

def make_commonerrors_tool():
    def commonerrors(null_arg):
        errors = """ 
        Here are some fixes to common errors. 
        Check that the query you tried doesn't make any of them and try the RunSparqlQuery tool again with a new query.

        1. If using feature make sure you access it with this: {?lcms enpkg:has_lcms_feature_list/enpkg:has_lcms_feature ?feature}
        2. URI with prefix should NOT be in quotation marks (don't do this - 'enpkg:npc_Saponaceolide_triterpenoids')
        """

        return errors

    errors_name = 'CommonErrorsTool'
    errors_desc = 'Useful if sparql query returned no results to self-correct'

    errors_tool = SimpleTool(errors_name, errors_desc, commonerrors)
    errors_tool.make_tool()
    return errors_tool



def make_tools(endpoint_url, local_files_dir = './', ClassDB=None, UnitDB=None):
    """
    Main function to build all tools for KGAI, specific to ENPKG

    endpoint_url: SPARQL endpoint
    local_files_dir: path to directory containing 'local_files/' directory. Include '/' at the end
    ClassDB: VectorDB of chemical class info that is preloaded (optional)
    UnitDB: VectorDB of unit info that is preloaded (optional)
    """
    run_sparql_query = make_runsparql_tool(endpoint_url)
    taxon_agent = make_taxon_tool(endpoint_url)
    NPCClass = make_chemicalclass_tool(local_files_dir = local_files_dir, ClassDB = ClassDB)
    target_agent = make_target_tool()
    structure_agent = make_structure_tool()
    unit_agent = make_unit_tool(local_files_dir = local_files_dir, UnitDB=UnitDB)
    schema_retriever_tool = make_schemaretriever_tool(local_files_dir = local_files_dir)
    errors_tool = make_commonerrors_tool()

    all_tools = [run_sparql_query.tool,
                 taxon_agent.tool,
                 NPCClass.tool,
                 target_agent.tool,
                 structure_agent.tool,
                 unit_agent.tool,
                 schema_retriever_tool.tool,
                 errors_tool.tool]
    
    return all_tools
