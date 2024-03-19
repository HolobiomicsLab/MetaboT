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
from custom_sqlite_streamlit import SqliteSaver

# langchain pydantic for base model definitions
from langchain.pydantic_v1 import BaseModel, Field

# langchain tools for base, structured tool definitions, and tool decorators
from langchain.tools import BaseTool, StructuredTool, tool

# Standard library import for object serialization
import pickle


####################### Instantiate the graph #######################
def create_rdf_graph():
    """
    Initializes an RdfGraph object with a specified query endpoint and a standard.

    Parameters:
    - endpoint_url (str): The URL of the query endpoint.

    Returns:
    - An instance of RdfGraph configured with the given query endpoint and 'rdf' as the standard.
    """
    endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    # Initialize the RdfGraph object with the given endpoint and the standard set to 'rdf'
    graph = RdfGraph(query_endpoint=endpoint_url, standard="rdf")
    with open("../graphs/graph.pkl", "wb") as output_file:
        pickle.dump(graph, output_file)

    print(graph.get_schema)
    return graph


def create_chat_openai_instance(model_id):
    """
    Initializes a ChatOpenAI object with specified settings.
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


# Define a list of structured tools for chemical, taxon, target, and SMILES conversion resolution.
def tools_resolver_creator(llm):
    # Initialize chemical and taxon resolver tools with the llm model for specialized query processing.
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


def tool_sparql_creator(llm, graph):
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
def interpreter_logic(question, generated_sparql_query, file_path) -> None:
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
    print(f"Interpreting {question}")
    print(f"SPARQL query: {generated_sparql_query}")
    print(f"File path: {file_path}")
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


def tool_interpreter_creator():
    interpreter_tool = [
        StructuredTool.from_function(
            name="INTERPRETER_TOOL",
            func=interpreter_logic,
            description="The function takes an original user question, generated sparql query, and generated sparql query result stored in file_path and returns interpreted answer content",
            args_schema=InterpreterInput,
        )
    ]
    return interpreter_tool


def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    """
    Creates an AgentExecutor with LLM, set of tools, and system prompt.

    This function initializes a chat prompt template with a system message, placeholders for messages,
    and an agent scratchpad. It then creates an agent using the specified LLM and tools,
    and wraps this agent in an AgentExecutor for execution.

    Parameters:
    - llm (ChatOpenAI): The language model to be used by the agent for generating responses.
    - tools (list): A list of tools (functions or utilities) that the agent can use to perform actions or generate responses.
    - system_prompt (str): A string that provides initial instructions or information to the agent. This is used to set up the context for the agent's operations.

    Returns:
    - AgentExecutor: An executor object that manages the execution of the agent, allowing the agent to process input and use tools as defined.
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

    Parameters:
    - llm (ChatOpenAI): The language model to be used for processing and routing decisions.
    - system_prompt (str): A detailed prompt describing the supervisor's role and decision-making guidelines.
    - members (list): A list of specialized agents available for task delegation.

    Returns:
    - str: A configured prompt or agent setup that integrates routing logic for processing user questions.
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
def agent_node(state, agent, name):
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


##CHANGE IT
def process_stream(app, q2):
    try:
        # Iterate over the stream from app.stream()
        for s in app.stream(
            {
                "messages": [
                    HumanMessage(content=q2)  # Assuming q2 is the content of the message
                ]
            },
            {"configurable": {"thread_id": "2"}},  # Additional options for the stream
        ):
            # Check if "__end__" is not in the stream output
            if "__end__" not in s:
                print(s)  # Print the stream output
                print("----")  # Print the delimiter
    except Exception as e:
        print(f"An error occurred: {e}")


def create_run_agent(question):
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
    # Define the system message for the entity resolution agent (resolver) responsible for processing user questions.
    # This message includes instructions for the agent on how to handle different types of entities mentioned in questions.
    system_message_resolver = """You are an entity resolution agent for the Sparql_query_runner.
    You have access to the following tools:
    {tool_names}
    You should analyze the question and provide resolved entities to the supervisor. Here is a list of steps to help you accomplish your role:
    If the question ask anything about any entities that could be natural product compound, find the relevant IRI to this chemical class using CHEMICAL_RESOLVER. Input is the chemical class name. For example, if salicin is mentioned in the question, provide its IRI using CHEMICAL_RESOLVER, input is salicin. 

    If a taxon is mentionned, find what is its wikidata IRI with TAXON_RESOLVER. Input is the taxon name. For example, if the question mentions acer saccharum, you should provide it's wikidata IRI using TAXON_RESOLVER tool.")

    If a target is mentionned, find the ChEMBLTarget IRI of the target with TARGET_RESOLVER. Input is the target name.

    If a SMILE structure is mentionned, find what is the InChIKey notation of the molecule with SMILE_CONVERTER. Input is the SMILE structure. For example, if there is a string with similar structure to CCC12CCCN3C1C4(CC3) in the question, provide it to SMILE_CONVERTER.
        
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

    If you have answers from the agent mentioned above, you provide those answers with the user question to the Sparql_query_runner.

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

    # creating nodes for each agent
    enpkg_node = functools.partial(agent_node, agent=enpkg_agent, name="ENPKG_agent")
    sparql_query_node = functools.partial(
        agent_node, agent=sparql_query_agent, name="Sparql_query_runner"
    )
    interpreter_agent_node = functools.partial(
        agent_node, agent=interpreter_agent, name="Interpreter_agent"
    )
    supervisor_agent = create_team_supervisor(llm_gpt4, system_prompt, members)

    # creating the workflow and adding nodes to it
    workflow = create_workflow()

    workflow.add_node("ENPKG_agent", enpkg_node)
    workflow.add_node("Sparql_query_runner", sparql_query_node)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("Interpreter_agent", interpreter_agent_node)

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

    workflow.set_entry_point("supervisor")
    app = workflow.compile(checkpointer=memory)
    result = process_stream(app, question)
    return result


print(
    create_run_agent("How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?")
)
