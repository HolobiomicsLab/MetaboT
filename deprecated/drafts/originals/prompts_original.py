from langchain.prompts.prompt import PromptTemplate

### SCHEMA PROMPT ######################
default_prompt_template_w_schema = """
You are trying to answer a question using the Experiment Natural Products Knowledge Graph (ENPKG). Here are your instructions:

1. ONLY IF a taxon is mentioned, use TaxonTool. 
2. ONLY IF a chemical class is mentioned, use ClassTool
3. ONLY IF a target is mentioned, use TargetTool
4. ONLY IF a numerical value is mentioned, use UnitTool
5. ONLY IF a SMILES structure is mentioned, use StructureTool
6. Run sparql query with SparqlQueryRunner Tool
7. ONLY IF no results, use ErrorsTool
8. Repeat steps 6-7 at most 3 times
9. Tell the user how to improve their question and give the SPARQL query you tried.

Note: Input to TaxonTool is colon-seperated list of the taxon and the original question.
Note: No input needed for SchemaRetrieverTool and ErrorsTool
Note: Input to UnitTool is the entire question 

Use the schema below for identifying relavent URIs and to understand instances of what classes or related to others. Here is the schema of ENPKG is .ttl format. The entities listed indicate the type of objects that the predicates relate.
{schema}

You can use these prefixes:
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>

Question: {question}
"""

### DEFAULT PROMPT #######################

default_prompt_template = """
You are trying to answer a question using the Experiment Natural Products Knowledge Graph (ENPKG). Here are your instructions:

1. ONLY IF a taxon is mentioned, use TaxonTool. 
2. ONLY IF a chemical class is mentioned, use ClassTool
3. ONLY IF a target is mentioned, use TargetTool
4. ONLY IF a numerical value is mentioned, use UnitTool
5. ONLY IF a SMILES structure is mentioned, use StructureTool
6. Retrieve rest of schema with SchemaRetrieverTool and use to identify relavent URIs and to understand instances of what classes are related to others.
7. Run sparql query with SparqlQueryRunner Tool
8. ONLY IF no results, use ErrorsTool
9. Repeat steps 7-8 at most 3 times
10. Tell the user how to improve their question and give the SPARQL query you tried.

Note: Input to TaxonTool is colon-seperated list of the taxon and the original question.
Note: No input needed for SchemaRetrieverTool and ErrorsTool
Note: Input to UnitTool is the entire question 

You can use these prefixes:
PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>
PREFIX enpkg_module: <https://enpkg.commons-lab.org/module/>

Question: {question}
"""
#Note: URIs without prefix substitutions should be between < >

default_prompt = PromptTemplate(
    template=default_prompt_template,
    input_variables=["question"]
)

### TOOL PROMPTS ############################
# Chemical Class prompt
chemical_class_template = """
Give me npc_class uris relevant to this chemical class: {question}. Return nothing if the question don't ask anything about
any entities that could be classes. Return the uri + the prefix: 'enpkg:'
"""

# Taxon Agent prompt
taxon_agent_template = """
Find the best uri for {input} using the tools available: \
1. TaxonLookup

Return the best uri in context of this question ({question}) and say that it is an instance of the class – https://enpkg.commons-lab.org/kg/LabExtract.
URI should be used in the following way:
?extract a enpkg:LabExtract
FILTER(?extract = taxon_uri)
"""

# Target Agent prompt
target_prompt_template = """For this target: {input}, what is the most relevant target name? 
'Leishmania donovani', 'Trypanosoma cruzi', 'Trypanosoma brucei rhodesiense'
Answer with either one of those 3 options or say there is no relevant target name. Also included that it should be used in the following way:
?chembl_assay_results enpkg_module:target_name target
""" 

# Structure Agent prompt
structure_agent_template = """
Instructions:
1. Check if input is a SMILES chemical structure. If yes continue, else say that the input is not a SMILES so need to ask user for the SMILES.
2. Run the tool StructureQueryTool with the input.
3. Return SPARQL subquery. 
Input: {input}
"""

# Unit Tool prompt
unit_template = """
Give me units relevant to numerical values in this question: {question}. Return nothing if units for value is not provided.
Be sure to say that these are the units of the quantities found in the knowledge graph.
"""

unit_prompt = PromptTemplate(
    input_variables=['question'], 
    template=unit_template
)