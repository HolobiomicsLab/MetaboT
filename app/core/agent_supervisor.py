# langchain imports for agent and prompt handling
import functools
import logging.config
import operator
import os

# Standard library import for object serialization
import pickle
from pathlib import Path

# typing imports for type hinting
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

from chemical_resolver import ChemicalResolver
from codeinterpreterapi import CodeInterpreterSession, File
from custom_sqlite_file import SqliteSaver
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.chains.llm import LLMChain

# langchain output parser for OpenAI functions
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.prompts import BaseChatPromptTemplate

# langchain pydantic for base model definitions
from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema import AgentAction, AgentFinish, HumanMessage

# langchain tools for base, structured tool definitions, and tool decorators
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.utilities import SerpAPIWrapper

# langchain_core imports for message handling and action schema
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# langgraph imports for prebuilt tool invocation
from langgraph.prebuilt import ToolInvocation
from log_search import LogMemoryAccessTool
from prompts import (
    ENPKG_AGENT_PROMPT,
    ENTRY_AGENT_PROMPT,
    INTERPRETER_AGENT_PROMPT,
    SPARQL_AGENT_PROMPT,
    SUPERVISOR_AGENT_PROMPT,
)

# Custom imports for RDF graph manipulation and chemical, target, taxon, and SPARQL resolution
from RdfGraphCustom import RdfGraph
from smile_resolver import smiles_to_inchikey
from sparql import GraphSparqlQAChain
from target_resolver import target_name_to_target_id
from taxon_resolver import TaxonResolver

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
def agent_node(state, agent, name: str) -> Dict[str, Any]:
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


# TODO: CHANGE IT
# TODO: docstring
def process_stream(app: StateGraph, q: str, thread_id: int) -> NoReturn:
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


def create_agents():
    """Creates and initializes agents for a workflow.

    Initializes various agents required for managing a question-answering or information processing
    workflow. This includes creating instances for different roles such as SPARQL query runners,
    code interpreter, entity resolution (ENPKG) agent, entry agent, and a supervisor agent.
    Each agent is initialized with specific models and tools necessary for its operation,
    including language models and utility tools for database access, RDF graph manipulation, etc.

    Returns:
        A dictionary mapping each agent's role (as a string) to its corresponding initialized agent object.
    """
    models = {
        "gpt4": create_chat_openai_instance("gpt-4"),
        "gpt4_preview": create_chat_openai_instance("gpt-4-0125-preview"),
    }

    graph = create_rdf_graph()
    tools = {
        "sparql": tool_sparql_creator(models["gpt4"], graph),
        "interpreter": tool_interpreter_creator(),
        "memory": memory_access_tool_creator(),
    }

    tools_resolver = tools_resolver_creator(models["gpt4_preview"])
    tool_names = [tool.name for tool in tools_resolver]

    system_messages = {
        "resolver": ENPKG_AGENT_PROMPT.format(tool_names="\n".join(tool_names)),
        "entry": ENTRY_AGENT_PROMPT.format(tool=tools["memory"].name),
    }

    agents = {
        "Sparql_query_runner": create_agent(
            models["gpt4_preview"], tools["sparql"], SPARQL_AGENT_PROMPT
        ),
        "Interpreter_agent": create_agent(
            models["gpt4_preview"], tools["interpreter"], INTERPRETER_AGENT_PROMPT
        ),
        "ENPKG_agent": create_agent(
            models["gpt4_preview"], tools_resolver, system_messages["resolver"]
        ),
        "Entry_Agent": create_agent(
            models["gpt4"], [tools["memory"]], system_messages["entry"]
        ),
        "supervisor": create_team_supervisor(
            models["gpt4"],
            SUPERVISOR_AGENT_PROMPT,
            ["ENPKG_agent", "Sparql_query_runner", "Interpreter_agent"],
        ),
    }

    return agents


def manage_workflow(
    agents: Dict[str, AgentExecutor], question: str, thread_id: int = 1
):
    """Manages and executes a workflow with given agents.

    This function sets up a workflow for processing a question through various agents.
    It creates nodes for each agent, sets up the workflow, and then executes it by processing
    the provided question. The workflow consists of adding nodes for each agent, creating
    edges between agents and a supervisor, setting conditional edges for the workflow's logic,
    and finally compiling and running the workflow.

    Args:
        agents: A dictionary of agent names to their corresponding `AgentExecutor` instances.
            The dictionary must include a "supervisor" key for the supervisor agent.
        question: The question or input to be processed by the workflow.
        thread_id: An optional thread ID for the workflow execution, defaulting to 1.

    Returns:
        None. The function initiates processing of the stream but does not return any value.
        Outputs and logs from the agents are handled internally within the function.

    Raises:
        This function does not explicitly raise exceptions but exceptions can be raised
        internally within the workflow or agent execution processes.

    Example:
        >>> agents = {
            "Entry_Agent": entry_agent_executor,
            "ENPKG_agent": enpkg_agent_executor,
            "Sparql_query_runner": sparql_query_runner_executor,
            "Interpreter_agent": interpreter_agent_executor,
            "supervisor": supervisor_agent_executor
        }
        >>> manage_workflow(agents, "What is the capital of France?", thread_id=2)
    """
    workflow = create_workflow()

    # Create partial functions for nodes
    nodes = {
        name: functools.partial(agent_node, agent=agent, name=name)
        for name, agent in agents.items()
        if name != "supervisor"
    }
    nodes["supervisor"] = agents["supervisor"]

    # Add nodes to the workflow
    for name, node in nodes.items():
        workflow.add_node(name, node)

    for member in [
        "Entry_Agent",
        "ENPKG_agent",
        "Sparql_query_runner",
        "Interpreter_agent",
    ]:
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

    # Set entry point and compile
    workflow.set_entry_point("Entry_Agent")
    memory = SqliteSaver()
    app = workflow.compile(checkpointer=memory)
    process_stream(app, question, thread_id)


def create_and_run_agent(question: str, thread_id: int = 1):
    agents = create_agents()
    result = manage_workflow(agents, question, thread_id)
    return result

# Custom function for streamlit usage
def create_langgraph_app_streamlit(
    agents: Dict[str, AgentExecutor], memory: Any,
):
    """
    Modified version of the manage_workflow for streamlit. This function creates the langgraph app and defines the workflow.

    This function sets up a workflow for processing a question through various agents.
    It creates nodes for each agent, sets up the workflow, and then executes it by processing
    the provided question. The workflow consists of adding nodes for each agent, creating
    edges between agents and a supervisor, setting conditional edges for the workflow's logic,
    and finally compiling and returning the workflow.

    Args:
        agents: A dictionary of agent names to their corresponding `AgentExecutor` instances.
            The dictionary must include a "supervisor" key for the supervisor agent.
        memory: Memory initialized in the streamlit app.

    Returns:
        App. The function creates the app with the agents allowing the streaming of outputs in Streamlit

    Raises:
        This function does not explicitly raise exceptions but exceptions can be raised
        internally within the workflow or agent execution processes.

    Example:
        >>> agents = {
            "Entry_Agent": entry_agent_executor,
            "ENPKG_agent": enpkg_agent_executor,
            "Sparql_query_runner": sparql_query_runner_executor,
            "Interpreter_agent": interpreter_agent_executor,
            "supervisor": supervisor_agent_executor
        }
        >>> manage_workflow(agents, "What is the capital of France?", thread_id=2)
    """
    workflow = create_workflow()

    # Create partial functions for nodes
    nodes = {
        name: functools.partial(agent_node, agent=agent, name=name)
        for name, agent in agents.items()
        if name != "supervisor"
    }
    nodes["supervisor"] = agents["supervisor"]

    # Add nodes to the workflow
    for name, node in nodes.items():
        workflow.add_node(name, node)

    for member in [
        "Entry_Agent",
        "ENPKG_agent",
        "Sparql_query_runner",
        "Interpreter_agent",
    ]:
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

    # Set entry point and compile
    workflow.set_entry_point("Entry_Agent")
    memory = memory
    app = workflow.compile(checkpointer=memory)
    return app

if __name__ == "__main__":

    # run with CLI ```python agent_supervisor.py````

    # TODO: [Benjamin] questions should be in a configuration file?

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

    logger.info(create_and_run_agent(question=q5_bis, thread_id=1))
