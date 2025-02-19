# langchain imports for agent and prompt handling
import functools
import operator
from typing import (
    Annotated,
    Any,
    Dict,
    NoReturn,
    Sequence,
    TypedDict,
    Literal,
    Optional,
)
import pickle
from pathlib import Path

from langchain.schema import HumanMessage
from langchain.agents import AgentExecutor
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph

from app.core.memory.database_manager import memory_database, tools_database
from app.core.utils import load_config, setup_logger
from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.agents.agents_factory import create_all_agents
from app.core.llm_handler import llm_creation

logger = setup_logger(__name__)
parent_dir = Path(__file__).resolve().parent.parent.parent

class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str

def link_kg_database(endpoint_url: str):
    """
    Checks if an RDF graph is already created, and if not, it initializes and saves a new RDF graph object using a specified endpoint URL.

    Returns:
        RdfGraph: An RDF graph object.
    """

    graph_path = parent_dir / "graphs" / "graph.pkl"

    # check if the graph is already created if not create it.
    try:
        with open(graph_path, "rb") as input_file:
            graph = pickle.load(input_file)
            # logger.info(f"schema: {graph.get_schema}")
            return graph
    except FileNotFoundError:
        pass

    # Initialize the RdfGraph object with the given endpoint and the standard set to 'rdf'
    graph = RdfGraph(query_endpoint=endpoint_url, standard="rdf")

    with open(graph_path, "wb") as output_file:
        pickle.dump(graph, output_file)
    # logger.info(f"schema: {graph.get_schema}")
    return graph

def create_workflow(
    api_key: str,
    session_id: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    evaluation: bool = False
) -> StateGraph:
    """
    Create a unified workflow that internally manages agents, models, and graphs.
    This function combines the functionality previously split across different files.

    Args:
        api_key (str): OpenAI API key for model creation
        session_id (Optional[str]): Session ID for memory management
        endpoint_url (Optional[str]): URL for the knowledge graph endpoint
        evaluation (bool): Whether to run in evaluation mode

    Returns:
        StateGraph: The compiled workflow
    """
    # Initialize the graph
    if endpoint_url is None:
        endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    
    graph = link_kg_database(endpoint_url)
    
    # Create models with the provided API key
    
    models = llm_creation(api_key=api_key)
    
    # Create agents with the initialized components
    agents = create_all_agents(
        llms=models,
        graph=graph,
        openai_key=api_key,
        session_id=session_id
    )

    # Initialize workflow
    workflow = StateGraph(AgentState)

    # Load configuration
    config = load_config()

    # Add nodes to the workflow based on JSON configuration
    for node_config in config["agents"]:
        node_id = node_config["name"]
        if node_id != "supervisor":
            node = functools.partial(agent_node, agent=agents[node_id], name=node_id)
        else:
            node = agents["supervisor"]
        workflow.add_node(node_id, node)

    # Add static edges based on JSON configuration
    for edge in config["edges"]:
        workflow.add_edge(edge["source"], edge["target"])

    # Add conditional edges based on JSON configuration
    for cond_edge in config["conditional_edges"]:
        if cond_edge["source"] == "supervisor":
            workflow.add_conditional_edges(
                cond_edge["source"],
                lambda x: x["next"],
                {
                    target["condition_value"]: target["target"]
                    for target in cond_edge["targets"]
                },
            )

        if cond_edge["source"] == "Validator":
            workflow.add_conditional_edges(
                cond_edge["source"],
                router,
                {
                    target["condition_value"]: target["target"]
                    for target in cond_edge["targets"]
                },
            )

        elif cond_edge["source"] == "Entry_Agent":
            workflow.add_conditional_edges(
                cond_edge["source"],
                router_entry,
                {
                    target["condition_value"]: target["target"]
                    for target in cond_edge["targets"]
                },
            )


    try:
        db_manager = tools_database()
        db_manager.initialize_db()
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    # Set entry point
    workflow.set_entry_point("Entry_Agent")

    # Compile workflow based on mode
    if evaluation:
        app = workflow.compile()

    else:
        memory = memory_database()
        app = workflow.compile(checkpointer=memory)

    return app

def agent_node(state, agent, name: str) -> Dict[str, Any]:
    """Execute an agent node in the workflow."""
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

def router(state) -> Literal["supervisor", "__end__"]:
    """Route messages based on validation results."""
    messages = state["messages"]
    last_message = messages[-1]

    if "The question is valid" in last_message.content:
        return "supervisor"
    return "__end__"

def router_entry(state) -> Literal["supervisor", "Validator"]:
    """Route entry messages to appropriate handlers."""
    messages = state["messages"]
    last_message = messages[-1]

    if "Calling the supervisor" in last_message.content:
        return "supervisor"
    return "Validator"

def process_workflow(app: StateGraph, question: str, thread_id: int = 1) -> NoReturn:
    """Process a workflow with the given question."""
    try:
        for s in app.stream(
            {
                "messages": [
                    HumanMessage(content=question)
                ]
            },
            {
                "configurable": {"thread_id": thread_id}
            },
        ):
            if "__end__" not in s:
                logger.info(s)
                logger.info("----")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

