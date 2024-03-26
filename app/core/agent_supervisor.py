# langchain imports for agent and prompt handling
from langchain.agents import AgentExecutor
from langchain.prompts import BaseChatPromptTemplate
from langchain.utilities import SerpAPIWrapper
from langchain.chains.llm import LLMChain
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent
from langchain import hub

# langgraph imports for prebuilt tool invocation
from langgraph.prebuilt import ToolInvocation
from langgraph.graph import StateGraph, END

# langchain_core imports for message handling and action schema
from langchain_core.messages import BaseMessage, HumanMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AgentAction, AgentFinish, HumanMessage

# langchain output parser for OpenAI functions
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from codeinterpreterapi import CodeInterpreterSession, File

# typing imports for type hinting
from typing import (
    Annotated,
    List,
    Tuple,
    Union,
    Any,
    Dict,
    Optional,
    Sequence,
    TypedDict,
)
import operator
import functools

# Custom imports for RDF graph manipulation and chemical, target, taxon, and SPARQL resolution
from RdfGraphCustom import RdfGraph
from smile_resolver import smiles_to_inchikey
from chemical_resolver import ChemicalResolver
from target_resolver import target_name_to_target_id
from taxon_resolver import TaxonResolver
from sparql import GraphSparqlQAChain
from custom_sqlite_file import SqliteSaver
from log_search import LogMemoryAccessTool

# langchain pydantic for base model definitions
from langchain.pydantic_v1 import BaseModel, Field

# langchain tools for base, structured tool definitions, and tool decorators
from langchain.tools import BaseTool, StructuredTool, tool

# Standard library import for object serialization
import pickle
from pathlib import Path
import logging.config

parent_dir = Path(__file__).parent.parent
config_path = parent_dir / "config" / "logging.ini"
logging.config.fileConfig(config_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)



####################### Instantiate the graph #######################
def create_rdf_graph():
    """
    Checks if an RDF graph is already created, and if not, it initializes and saves a new RDF graph object using a specified endpoint URL.

    Returns:
        RdfGraph: An RDF graph object.
    """

    ## check if the graph is already created if not create it.
    try:
        with open("../graphs/graph.pkl", "rb") as input_file:
            graph = pickle.load(input_file)
            logger.info(f"schema: {graph.get_schema}")
            return graph
    except FileNotFoundError:
        pass

    endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"

    # Initialize the RdfGraph object with the given endpoint and the standard set to 'rdf'
    graph = RdfGraph(query_endpoint=endpoint_url, standard="rdf")

    with open("../graphs/graph.pkl", "wb") as output_file:
        pickle.dump(graph, output_file)
    logger.info(f"schema: {graph.get_schema}")
    return graph


def create_chat_openai_instance(model_id: str) -> ChatOpenAI:
    """
    Creates an instance of the ChatOpenAI class with specified parameters.

    Args:
      model_id (str): The identifier of the OpenAI model.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI class.
    """
    temperature = 0
    llm = ChatOpenAI(
        temperature=temperature, model=model_id, max_retries=3, verbose=True
    )
    return llm


# Pydantic models for structured input to the resolver tools.


class ChemicalInput(BaseModel):
    query: str = Field(description="natural product compound string")


class SparqlInput(BaseModel):
    question: str = Field(description="the original question from the user")
    entities: str = Field(
        description="strings containing for all entities, entity name and the corresponding entity identifier"
    )


class InterpreterInput(BaseModel):
    question: str = Field(description="the original question from the user")
    generated_sparql_query: str = Field(description="the generated SPARQL query")
    file_path: str = Field(
        description="file path where result of generated SPARQL query is stored"
    )


class QueryInput(BaseModel):
    query: str = Field(description="Query string to search in memory logs.")


def tools_resolver_creator(llm: ChatOpenAI) -> List[StructuredTool]:
    """
    Creates a list of structured tools for resolving chemical, taxonomic, target, and SMILES data.

    Args:
      llm (ChatOpenAI): The language model instance used for generating responses.

    Returns:
      list[StructuredTool]: A list of structured tools for resolving chemical, taxonomic, target, and SMILES data.
    """
    chem_res = ChemicalResolver.from_llm(llm=llm, verbose=True)
    taxon_res = TaxonResolver()

    tools_resolver = [
        StructuredTool.from_function(
            name="CHEMICAL_RESOLVER",
            func=chem_res.run,
            description="The function takes a natural product compound string as input and returns a InChIKey, if InChIKey not found, it returns the NPCClass, NPCPathway or NPCSuperClass.",
            args_schema=ChemicalInput,
        ),
        StructuredTool.from_function(
            name="TAXON_RESOLVER",
            func=taxon_res.query_wikidata,
            description="The function takes a taxon string as input and returns the wikidata ID.",
        ),
        StructuredTool.from_function(
            name="TARGET_RESOLVER",
            func=target_name_to_target_id,
            description="The function takes a target string as input and returns the ChEMBLTarget IRI.",
        ),
        StructuredTool.from_function(
            name="SMILE_CONVERTER",
            func=smiles_to_inchikey,
            description="The function takes a SMILES string as input and returns the InChIKey notation of the molecule.",
        ),
    ]

    return tools_resolver


def tool_sparql_creator(llm: ChatOpenAI, graph: RdfGraph) -> list[StructuredTool]:
    """
    Creates a structured tool for running SPARQL queries using a given ChatOpenAI instance and RDF graph.

    Args:
      llm (ChatOpenAI): the language model instance used for generating queries.
      graph (RdfGraph): the RDF graph object used for querying.
    Returns:
      list[StructuredTool]: A list of structured tools for running SPARQL queries.
    """

    sparql_chain = GraphSparqlQAChain.from_llm(llm, graph=graph, verbose=True)

    tool_sparql = [
        StructuredTool.from_function(
            name="SPARQL_QUERY_RUNNER",
            func=sparql_chain.run,
            description="The agent resolve the user's question by querying the knowledge graph database. Input should be a question and the resolved entities in the question.",
            args_schema=SparqlInput,
            # return_direct=True,
        )
    ]
    return tool_sparql


# Define a tool for interpreter agent
def interpreter_logic(
    question: str, generated_sparql_query: str, file_path: str
) -> None:
    """Interprets the results of a SPARQL query based on user's question.

    Args:
        question (str): The original question from the user.
        generated_sparql_query (str): The generated SPARQL query.
        file_path (str): The file path where the result of the generated SPARQL query is stored.

    Returns:
        None: Outputs the response after interpreting the SPARQL results.
    """
    # context manager for start/stop of the session
    # define the user request
    logger.info(f"Interpreting {question}")
    logger.info(f"SPARQL query: {generated_sparql_query}")
    logger.info(f"File path: {file_path}")
    with CodeInterpreterSession() as session:
        user_request = f"""You are an interpreter agent. Your task is to analyze the output related to a SPARQL query, which could be in two forms:
         If the output of the Sparql_query_runner agent is only the dictionary containing question: "{question}", generated SPARQL query: "{generated_sparql_query}" which was used to query the knowledge graph to answer to the question and path: "{file_path}" containing the SPARQL output then you should review the provided dataset from the file and SPARQL query to provide a clear, concise answer to the question. Additionally, if visualization of the results is necessary (e.g., when the SPARQL output is large or complex), you should provide an appropriate visualization, such as a bar chart, diagram, or plot, to effectively communicate the answer.
         If the output of the Sparql_query_runner agent contains the answer to the question together with the dictionary containing the question: "{question}", generated SPARQL query: "{generated_sparql_query}" and path: "{file_path}", then you should analyze this output and provide visualization of the answer to the question. 
         The type of visualization – bar chart, diagram, or plot – will depend on the nature of the SPARQL output and the best way to represent the answer to the question clearly.
         Submit only the final answer to the supervisor. Indicate the format of the dataset for appropriate handling. """
        files = [
            File.from_path(file_path),
        ]

        # generate the response
        response = session.generate_response(user_request, files=files)
        # output the response (text + image)
        response.show()
        return response.content


def tool_interpreter_creator() -> list[StructuredTool]:
    """
    Creates an interpreter tool for processing user questions and SparQL queries.
    
    Returns:
      list[StructuredTool]: A list of structured tools for interpreting user questions and SparQL queries.
    """
    interpreter_tool = [
        StructuredTool.from_function(
            name="INTERPRETER_TOOL",
            func=interpreter_logic,
            description="The function takes an original user question, generated sparql query, and generated sparql query result stored in file_path and returns interpreted answer content",
            args_schema=InterpreterInput,
        )
    ]
    return interpreter_tool


def memory_access_tool_creator() -> StructuredTool:
    """
    Creates a structured tool for generating answers based on
    logs.
    
    Returns:
      StructuredTool: A structured tool for generating answers based on logs.
    """
    # Function adjusted to accept keyword arguments
    def memory_tool(**kwargs) -> Dict[str, Any]:
        # Create a QueryInput instance from kwargs
        query_input = QueryInput(**kwargs)

        # Instantiate LogMemoryAccessTool with its default parameters
        new_memory_tool_instance = LogMemoryAccessTool()

        # Directly use the generated answer method since we're focusing on generating responses
        return new_memory_tool_instance.generate_answer(query_input=query_input)

    # Assuming StructuredTool and its usage is similar to how you'd implement it based on your framework or requirements
    new_memory_access_tool = StructuredTool.from_function(
        name="NEW_MEMORY_ACCESS_QUERY_RUNNER",
        func=memory_tool,
        description="Generates an answer based on the logs and the provided query without explicitly calling the input.",
        args_schema=QueryInput,  # Ensure this matches your expected input schema
    )

    return new_memory_access_tool


def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str) -> AgentExecutor:
    """
    Creates an AgentExecutor with LLM, set of tools, and system prompt.

    This function initializes a chat prompt template with a system message, placeholders for messages,
    and an agent scratchpad. It then creates an agent using the specified LLM and tools,
    and wraps this agent in an AgentExecutor for execution.

    Args:
        llm (ChatOpenAI): The language model to be used by the agent for generating responses.
        tools (list): A list of tools (functions or utilities) that the agent can use to perform actions or generate responses.
        system_prompt (str): A string that provides initial instructions or information to the agent. This is used to set up the context for the agent's operations.

    Returns:
        AgentExecutor: An executor object that manages the execution of the agent, allowing the agent to process input and use tools as defined.
    """

    # Initialize a ChatPromptTemplate with a system message, placeholders for incoming messages, and an agent scratchpad.
    # This template structures the input to the language model, integrating static and dynamic content.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create an agent using the provided language model, tools, and the structured prompt.
    # This agent can interact with users, process input, and use tools based on the prompt template.
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Initialize an AgentExecutor to manage and execute the agent's operations.
    # The executor facilitates the interaction between the agent and the tools, handling execution logic.
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor


# Function to create a team supervisor agent that routes tasks based on user questions.
def create_team_supervisor(llm: ChatOpenAI, system_prompt, members) -> str:
    """
    Configures and returns a supervisor agent setup with decision-making logic for task routing.

    The supervisor uses a provided language model (llm) to analyze user questions and decides whether to delegate
    the question to specialized agents (members), or to mark the process as finished based on predefined criteria.

    Args:
        llm (ChatOpenAI): The language model to be used for processing and routing decisions.
        system_prompt (str): A detailed prompt describing the supervisor's role and decision-making guidelines.
        members (list): A list of specialized agents available for task delegation.

    Returns:
        str: A configured prompt or agent setup that integrates routing logic for processing user questions.
    """
    options = ["FINISH"] + members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))
    return (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )


# function to define nodes
# TODO: tell the state, agent and name types in the function signature (name ok)
def agent_node(state, agent, name : str) -> Dict[str, Any]:
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}


class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str


def create_workflow():
    workflow = StateGraph(AgentState)
    return workflow


#TODO: CHANGE IT
#TODO: docstring
def process_stream(app, q, thread_id):
    try:
        # Iterate over the stream from app.stream()
        for s in app.stream(
            {
                "messages": [
                    HumanMessage(content=q)  # Assuming q2 is the content of the message
                ]
            },
            {
                "configurable": {"thread_id": thread_id}
            },  # Additional options for the stream
        ):
            # Check if "__end__" is not in the stream output
            if "__end__" not in s:
                logger.info(s)  # logger.info the stream output
                logger.info("----")  # logger.info the delimiter
    except Exception as e:
        logger.error(f"An error occurred: {e}")

#TODO: what is the type of return value?
#TODO [Benjamin]: quite a long function. Can we break it down? prompts are constants, should be in configuration file
def create_run_agent(question : str, thread_id : int =1):
    model_id_gpt4 = "gpt-4"
    model_id = "gpt-4-0125-preview"
    llm = create_chat_openai_instance(
        model_id
    )  # Instance for GPT-4 0125-preview model.
    llm_gpt4 = create_chat_openai_instance(model_id_gpt4)
    graph = create_rdf_graph()
    tools_resolver = tools_resolver_creator(llm)
    tool_sparql = tool_sparql_creator(llm_gpt4, graph)
    tool_names = [
        tool.name for tool in tools_resolver
    ]  # List of tool names from the resolver tools.
    # tool for Interpreter_agent
    interpreter_session = CodeInterpreterSession()
    tool_interpreter = tool_interpreter_creator()
    tool_memory = memory_access_tool_creator()
    thread_id = thread_id

    # Define the system message for the entity resolution agent (resolver) responsible for processing user questions.
    # This message includes instructions for the agent on how to handle different types of entities mentioned in questions.
    system_message_resolver = """You are an entity resolution agent for the Sparql_query_runner.
    You have access to the following tools:
    {tool_names}
    You should analyze the question and provide resolved entities to the supervisor. Here is a list of steps to help you accomplish your role:
    If the question ask anything about any entities that could be natural product compound, find the relevant IRI to this chemical class using CHEMICAL_RESOLVER. Input is the chemical class name. For example, if salicin is mentioned in the question, provide its IRI using CHEMICAL_RESOLVER, input is salicin. 

    If a taxon is mentioned, find what is its wikidata IRI with TAXON_RESOLVER. Input is the taxon name. For example, if the question mentions acer saccharum, you should provide it's wikidata IRI using TAXON_RESOLVER tool.

    If a target is mentioned, find the ChEMBLTarget IRI of the target with TARGET_RESOLVER. Input is the target name.

    If a SMILE structure is mentioned, find what is the InChIKey notation of the molecule with SMILE_CONVERTER. Input is the SMILE structure. For example, if there is a string with similar structure to CCC12CCCN3C1C4(CC3) in the question, provide it to SMILE_CONVERTER.
        
    Give me units relevant to numerical values in this question. Return nothing if units for value is not provided.
    Be sure to say that these are the units of the quantities found in the knowledge graph.
    Here is the list of units to find:
    "retention time": "minutes",
    "activity value": null, 
    "feature area": "absolute count or intensity", 
    "relative feature area": "normalized area in percentage", 
    "parent mass": "ppm (parts-per-million) for m/z",
    "mass difference": "delta m/z", 
    "cosine": "score from 0 to 1. 1 = identical spectra. 0 = completely different spectra"


     You are required to submit only the final answer to the supervisor. 
        
    """.format(
        tool_names="\n".join(tool_names)
    )

    # Create an agent for entity resolution based on the instructions provided in `system_message_resolver`.
    enpkg_agent = create_agent(llm, tools_resolver, system_message_resolver)

    # Create an agent for running SPARQL queries based on user requests and resolved entities provided by other agents.
    system_message_sparql = """You are SPARQL query runner, you take as input the user request and resolved entities provided by other agents, generate a SPARQL query, run it on the knowledge graph and answer to the question using SPARQL_QUERY_RUNNER tool.  

    If the output of the SPARQL_QUERY_RUNNER tool consists of only generated SPARQL query and path to the file containing the SPARQL output, you will need to generate a dictionary as output from your process. This dictionary should contain exactly three key-value pairs:
    question: The key should be a string named 'question' and the value should be the natural language question you were asked to translate into a SPARQL query.
    generated_sparql_query: The key should be a string named 'generated_sparql_query' and the value should be the SPARQL query you generated based on the natural language question.
    file_path: The key should be a string named 'file_path' and the value should be the absolute path to the file where the generated SPARQL query is saved. In this case provide the generated dictionary to the supervisor which would call the Interpreter agent to further interpret the results.

    If the output of the SPARQL_QUERY_RUNNER tool consists of generated SPARQL query, path to the file containing the SPARQL output and the SPARQL output then you need to generate the final answer to the question based on the SPARQL output. Provide the final answer to the question together with the dictionary containing the question, generated_sparql_query and file_path. The dictionary should contain exactly three key-value pairs:
    question: The key should be a string named 'question' and the value should be the natural language question you were asked to translate into a SPARQL query.
    generated_sparql_query: The key should be a string named 'generated_sparql_query' and the value should be the SPARQL query you generated based on the natural language question.
    file_path: The key should be a string named 'file_path' and the value should be the absolute path to the file where the generated SPARQL query is saved.
     Provide the final answer to the supervisor.
    """
    sparql_query_agent = create_agent(llm, tool_sparql, system_message_sparql)

    system_message_interpreter = """You are an interpreter agent. Your main role is to analyze outputs from the Sparql_query_runner agent using the INTERPRETER_TOOL. The outputs from the Sparql_query_runner agent can be of two types:

    The output is a dictionary containing 'question', 'generated_sparql_query', and 'file_path'. This typically happens when the Sparql_query_runner agent has executed a query to fetch results for a complex question. Your task is to provide this dictionary directly to the INTERPRETER_TOOL to get a concise answer. Ensure you format the dictionary correctly and include all necessary information so the INTERPRETER_TOOL can process it efficiently.

    The output directly contains the answer to the question but still comes within a dictionary that includes the 'question', 'generated_sparql_query', and 'file_path'. Even if the answer is directly provided, your role remains to pass this entire dictionary to the INTERPRETER_TOOL. The tool requires this structured input to validate and format the final answer properly.

    In both scenarios, your primary function is to ensure that the INTERPRETER_TOOL receives the necessary information in a structured dictionary format. This allows the tool to analyze the SPARQL query's output thoroughly and provide a clear, concise answer to the initial question."""

    interpreter_agent = create_agent(llm, tool_interpreter, system_message_interpreter)
    # Define a list of agent names that will be part of the supervisor system.
    members = ["ENPKG_agent", "Sparql_query_runner", "Interpreter_agent"]

    # Define the system prompt that outlines the role and responsibilities of the supervisor agent,
    # including instructions on how to delegate tasks to specialized agents based on the user's question.
    system_prompt = """You are a supervisor. As the supervisor, your primary role is to coordinate the flow of information between agents and ensure the appropriate processing of the user question based on its content. You have access to a team of specialized agents: {members}.

    Here is a list of steps to help you accomplish your role:

    Analyse the user question and delegate functions to the specialized agents below if needed:
    If the question mentions any of the following entities: natural product compound, chemical name, taxon name, target, SMILES structure, or numerical value delegate the question to the ENPKG_agent. ENPKG_agent would provide resolved entities needed to generate SPARQL query. For example if the question mentions either caffeine, or Desmodium heterophyllum call ENPKG_agent.

    If you have answers from the agent mentioned above, you provide the exact answer without modification with the user question to the Sparql_query_runner.

    If the question does not mention chemical name, taxon name, target name, nor SMILES structure, delegate the question to the agent Sparql_query_runner. The Sparql_query_runner agent will perform further processing and provide the path containing the SPARQL output.

    If the Sparql_query_runner provides a SPARQL query and the path to the file containing the SPARQL output without directly providing the answer (implying that the answer is too long to be directly included), then delegate this information to the Interpreter_agent for further analysis and interpretation. Provide the Interpreter_agent with the question, SPARQL query, and the path to the file provided by the Sparql_query_runner. Await the Interpreter_agent's response for the final answer.

    Once the Interpreter_agent has completed its task mark the process as FINISH. Do not call the Interpreter_agent again.

    If the Sparql_query_runner agent provides a SPARQL query, the path to the file containing the SPARQL output and final answer to the question, and there is no immediate need for further interpretation, normally mark the process as FINISH. However, if there is a need to visualize the results (regardless of the length of the SPARQL output), also call the Interpreter_agent to generate the necessary plot, chart, or graph based on the SPARQL output. The need for visualization should be assessed based on the user's request or if the nature of the data implies that visualization would enhance understanding. Once the Interpreter_agent has completed its task mark the process as FINISH. Do not call the Interpreter_agent again.

    For example, the user provides the following question: For features from Melochia umbellata in PI mode with SIRIUS annotations, get the ones for which a feature in NI mode with the same retention time has the same SIRIUS annotation. Since the question mentions Melochia umbellata you should firstly delegate it to the ENPKG_agent which would provide wikidata IRI with TAXON_RESOLVER tool, then, you should delegate the question together with the output generated by ENPKG_agent to the Sparql_query_runner agent. Afterwards, if the Sparql_query_runner agent provided the answer to the question, SPARQL query and path to the file containing the SPARQL output and there is no need to visualize the output you should mark the process as FINISH. If the Sparql_query_runner agent  provided only SPARQL query and path to the file you should call Interpreter_agent which would interpret the results provided by Sparql_query_runner to generate the final response to the question.

    Avoid calling the same agent if this agent has already been called previously and provided the answer. For example, if you have called ENPKG_agent and it provided InChIKey for chemical compound do not call this agent again.

    Always tell the user the SPARQL query that has been returned by the Sparql_query_runner.

    If the agent does not provide the expected output mark the process as FINISH.

    Remember, your efficiency in routing the questions accurately and collecting responses is crucial for the seamless operation of our system. If you don't know the answer to any of the steps, please say explicitly and help the user by providing a query that you think will be better interpreted.
    """

    # Create an agent for entity resolution based on the instructions provided in `system_message_resolver`.
    enpkg_agent = create_agent(llm, tools_resolver, system_message_resolver)

    # Creating the Entry Agent prompt
    # 1. Determine if the question is within the knowledge domain of our system, which includes chemistry, natural products chemistry, mass spectrometry, biology, metabolomics, knowledge graphs, and related areas.
    entry_agent_prompt = """
    You are the first point of contact for user questions in a team of LLMs designed to answer technical questions involving the retrieval and interpretation of information from a Knowledge Graph Database of LC-MS Metabolomics of Natural Products. As the entry agent, you need to be very succint in your communications and answer only what you are instructed to. You should not answer questions out of your role. Your replies will be used by other LLMs as imputs, so it should strictly contain only what you are instructed to do.  

    Your role is to interpret the question sent by the user to you and to identify if the question is a "New Knowledge Question", a clarification you asked for a New Knowledge Question or a "Help me understand Question" and take actions based on this.

    A New Knowledge Question would be a question that requires information that you don't have available information at the moment and are not asking to explain results from previous questions. Those questions should be contained in the domains of Metabolomics, Chemistry, Mass Spectometry, Biology and Natural Products chemistry, and can include, for example, asking about compounds in a certain organism, to select and count the number of features containing a chemical entity, etc. If you identify that the question sent is a New Knowledge Question, you have to do the following:

    1. Check if the question requires clarification, focusing on these considerations:
        - ONLY IF common usual names are mentioned, there is need for clarification on the specific species or taxa, as common names could refer to multiple entities. Some examples are provided:
		-> The question "How many compounds annotated in positive mode in the extracts of mint contain a benzene substructure?" needs clarification since mint could refer to several species of the Mentha genus.
		-> The question "Select all compounds annotated in positive mode containing a benzene substructure" don't need specification, since it implies that it whishes to select all compounds containing the benzene substructure from all organisms.
        - ONLY IF the question includes unfinished scientific taxa specification, there is need for clarification only if the question implies specificity is needed. Some examples are provided:
		-> The question "Select all compounds from the genus Cedrus" don't need clarification since it is already specifying that wants all species in the Cedrus genus.
		-> The question "Which species of Arabidopsis contains more compounds annotated in negative mode in the database?" don't need clarification since it wants to compare all species from the genus Arabidopsis.
		-> The question "What compounds contain a spermidine substructure from Arabidopsis?" needs clarification since it don't implies that wants the genus and also don't specify the species. 
        - For questions involving ionization mode without specification, ask whether positive or negative mode information is sought, as the database separates these details. If no ionization mode is specified, this implies that the question is asking for both positive and negative ionization mode. 
        - Remember: If the question does not mention a specific taxa and the context does not imply a need for such specificity, assume the question is asking for all taxa available in the database. There is no need for clarification in such cases.
        - Similarly, if a chemical entity isn't specified, assume the query encompasses all chemical entities within the scope of the question. 

    2. If you detected that there's need for clarification, you have to reply what information do you want to be more precise. If there's no need for clarification, reply "Starting the processing of the question"
    3. When the user clarified your previous doubt, you have to now reply the original question and the clarification, as your answer will be used by the next LLM.


    A "Help me understand Question" would be a follow up question, asking for explaining or providing more information about any previous answer. In this case, you have to:  

    1. Utilize previous conversations stored in the your memory for context when replying to it, enabling more informed explanation about previous answers. If there's no information about it in your previous interactions, you should invoke your tool {tool} to search for information on the log. The input for the tool is what you want to search in the log. Use the answer given by the tool to help you reply back to the user. If there's also no information in the log, just reply that you don't have the information the user is looking for.

    You can also identify the need for transforming a "Help me understand question" in to a "New Knowledge Question". This would be a specific case when the user wants a explanation for a previous answer, but this explanation needs new information, that has to be searched on the database. In this case, you can formulate a question to be searched in the database based on previous conversation and the new information needed. 

    If the question is outside of your knowledge or scope, don't reply anything. Other members of your team will tackle the issue.

    """.format(
        tool=tool_memory.name
    )

    entry_agent = create_agent(llm_gpt4, [tool_memory], entry_agent_prompt)

    # creating nodes for each agent
    enpkg_node = functools.partial(agent_node, agent=enpkg_agent, name="ENPKG_agent")
    entry_node = functools.partial(agent_node, agent=entry_agent, name="Entry_Agent")
    sparql_query_node = functools.partial(
        agent_node, agent=sparql_query_agent, name="Sparql_query_runner"
    )
    interpreter_agent_node = functools.partial(
        agent_node, agent=interpreter_agent, name="Interpreter_agent"
    )
    supervisor_agent = create_team_supervisor(llm_gpt4, system_prompt, members)

    # creating the workflow and adding nodes to it
    workflow = create_workflow()

    workflow.add_node("Entry_Agent", entry_node)
    workflow.add_node("ENPKG_agent", enpkg_node)
    workflow.add_node("Sparql_query_runner", sparql_query_node)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("Interpreter_agent", interpreter_agent_node)

    # Adding entry as a node to supervisor
    workflow.add_edge("Entry_Agent", "supervisor")

    # connect all the edges in the graph
    for member in members:
        # We want our workers to ALWAYS "report back" to the supervisor when done
        workflow.add_edge(member, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "ENPKG_agent": "ENPKG_agent",
            "Sparql_query_runner": "Sparql_query_runner",
            "Interpreter_agent": "Interpreter_agent",
            "FINISH": END,
        },
    )

    memory = SqliteSaver()

    workflow.set_entry_point("Entry_Agent")
    app = workflow.compile(checkpointer=memory)
    result = process_stream(app, question, thread_id)
    return result


if __name__ == "__main__":

    # run with CLI ```python agent_supervisor.py````
    
    #TODO: [Benjamin] questions should be in a configuration file?

    q1 = "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey of the annotations?"
    q1_bis = "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?"
    q2 = "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids? Group by extract."
    q3 = "Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure?"
    q4 = "Among the SIRIUS structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract, which ones are reported in the Tabernaemontana genus in Wikidata?"
    q5 = "Which compounds have annotations with chembl assay results indicating reported activity against T. cruzi by looking at the cosmic, zodiac and taxo scores?"
    q5_bis = "Which compounds have annotations with chembl assay results indicating reported activity against Trypanosoma cruzi by looking at the cosmic, zodiac and taxo scores?"
    q6 = "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- adduct (+/- 5ppm)."
    q7 = "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D"
    q8 = "Which features were annotated as 'Tetraketide meroterpenoids' by SIRIUS, and how many such features were found for each species and plant part?"
    q9 = "What are all distinct submitted taxons for the extracts in the knowledge graph?"
    q10 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q11 = "Count all the species per family in the collection"

    q12 = "Taxons can be found in enpkg:LabExtract. Find the best URI of the Taxon in the context of this question : \n Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"
    q13 = "Which compounds annotated in the active extract of Melochia umbellata have activity against Trypanosoma cruzi reported (in ChEMBL)?"
    q14 = "What are the variations in the concentration of key active compounds found in Tabernaemontana coffeoides seed extracts across different sample collections?"
    q15 = "Which compounds are detected most in Tabernaemontana genus?"
    q16 = (
        "What are the most frequently detected compounds in the leaves of the Tabernaemontana genus? "
        " over of features annotated as certain chemical classes vary across different Tabernaemontana genus extracts in the ENPKG, with a focus on features identified in positive ionization mode and annotated by CANOPUS with a probability score above 0.5?"
    )
    q17 = " For all the plant extracts plot the distribution of number of features per sample retention time vs mass to charge ratio"
    q18 = "What are the most frequently observed chemical compounds in Tabernaemontana genus? Provide a bar chart."

    logger.info(create_run_agent(question=q5_bis, thread_id=1))
