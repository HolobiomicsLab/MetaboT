# langchain imports for agent and prompt handling
import functools
import operator

# Standard library import for object serialization

# typing imports for type hinting
from typing import (
    Annotated,
    Any,
    Dict,
    NoReturn,
    Sequence,
    TypedDict,
)

# langchain output parser for OpenAI functions

# langchain pydantic for base model definitions
from langchain.schema import HumanMessage
from langchain.agents import AgentExecutor

# langchain tools for base, structured tool definitions, and tool decorators

# langchain_core imports for message handling and action schema
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph

# langgraph imports for prebuilt tool invocation

from app.core.memory.custom_sqlite_file import SqliteSaver
from app.core.utils import setup_logger, load_config

logger = setup_logger(__name__)


class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str


def initiate_workflow():
    workflow = StateGraph(AgentState)
    return workflow


def process_workflow(app: StateGraph, question: str, thread_id: int = 1) -> NoReturn:
    try:
        # Iterate over the stream from app.stream()
        for s in app.stream(
            {
                "messages": [
                    HumanMessage(
                        content=question
                    )  # Assuming q2 is the content of the message
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


def agent_node(state, agent, name: str) -> Dict[str, Any]:
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}


def create_workflow(agents: Dict[str, AgentExecutor]) -> StateGraph:
    """
    Create a workflow based on a JSON configuration file, based on the agents provided and langGraph library.

    Args:
        agents (Dict[str, AgentExecutor]): list of agents to be used in the workflow

    Returns:
        StateGraph: The compiled workflow
    """

    config = load_config()

    workflow = initiate_workflow()

    # Add nodes to the workflow based on JSON configuration
    for node_config in config["nodes"]:
        node_id = node_config["id"]
        if node_id != "supervisor":
            node = functools.partial(
                agent_node, agent=agents[node_config["agent"]], name=node_id
            )
        else:
            node = agents["supervisor"]
        workflow.add_node(node_id, node)

    # Add static edges based on JSON configuration
    for edge in config["edges"]:
        workflow.add_edge(edge["source"], edge["target"])

    # Add conditional edges based on JSON configuration
    for cond_edge in config["conditional_edges"]:
        workflow.add_conditional_edges(
            cond_edge["source"],
            lambda x: x[cond_edge["condition"]],
            {
                target["condition_value"]: target["target"]
                for target in cond_edge["targets"]
            },
        )

    # Set entry point and compile
    workflow.set_entry_point("Entry_Agent")
    memory = SqliteSaver()
    app = workflow.compile(checkpointer=memory)
    return app
