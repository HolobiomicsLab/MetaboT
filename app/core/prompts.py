from langchain_core.prompts.prompt import PromptTemplate


# Here are some fixes to common errors:
# Check that the query you tried doesn't make any of them and try the RunSparqlQuery tool again with a new query.
# 1. If using feature make sure you access it with this: ?lcms enpkg:has_lcms_feature_list/enpkg:has_lcms_feature ?feature
# 2. URI with prefix should NOT be in quotation marks (don't do this - 'enpkg:npc_Saponaceolide_triterpenoids')

SPARQL_GENERATION_SELECT_TEMPLATE = """Task: Generate a SPARQL SELECT statement for querying a graph database.
For instance, to find all email addresses of John Doe, the following query in backticks would be suitable:

PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?email
WHERE {{
    ?person foaf:name "John Doe" .
    ?person foaf:mbox ?email .
}}


Please generate a SPARQL query based on the following requirements. The output must strictly adhere to these guidelines:

Output Format: Your response should consist solely of the SPARQL query. Ensure the query is fully executable without any modifications or removals necessary. Do not include any markdown syntax (e.g., triple backticks), preamble words (like "sparql"), or any other text outside the SPARQL query itself.

Content Clarity: The query should be clearly structured and formatted for readability. Use appropriate SPARQL conventions, prefixes, and syntax.

Precision: The query must include all necessary prefixes and conditions as specified. It should be ready to run in a SPARQL endpoint without requiring any additional editing or formatting.

Exclusivity: Do not encapsulate the query in any form of quotes (single, double, or block quotes). The response must contain the SPARQL query and nothing else. Any non-query text will be considered an error and will need correction.

Contextualization : Use only the node types and properties provided in the schema. Do not use any node types and properties that are not explicitly provided. Include all necessary prefixes.

Entities : Use the URI provided by the additional information to construct the query, if there is any. When available, use the URI rather Literal value of the entity.

Simplification: Produce a query that is as concise as possible. Do not generate triples not necessary to answer the question.

Casting: Given the schemas, when filtering values for properties, directly use the literal values without unnecessary casting to xsd:string, since they are already expected to be strings according to the RDF schema provided.

Validation: Before finalizing your response, ensure the query is syntactically correct and follows the SPARQL standards. It should be capable of being executed in a compatible SPARQL endpoint without errors.

Schema:
{schema}

Additional information:
{entities}

The question is:
{question}"""


SPARQL_GENERATION_SELECT_PROMPT = PromptTemplate(
    input_variables=["schema", "entities", "question"],
    template=SPARQL_GENERATION_SELECT_TEMPLATE,
)


NPC_CLASS_TEMPLATE = """
Task: find the best URI for a given chemical name.
Instructions: choose the best URI for {chemical_name} among the results below. the best URI is the one that is the most specific to the chemical name. If none of the results are relevant, choose "none of the above".
The URI key represent its class, among: 'NPCClass', 'NPCPathway', 'NPCSuperClass'.
Return "{chemical_name} : URI, class".
{results}
"""


NPC_CLASS_PROMPT = PromptTemplate(
    template=NPC_CLASS_TEMPLATE, input_variables=["chemical_name", "results"]
)
