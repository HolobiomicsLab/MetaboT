from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from app.core.agents.entry.entry_studio import ea_builder
from app.core.agents.validator.validator_studio import va_builder
from app.core.agents.supervisor.supervisor_studio import sa_builder
from app.core.agents.enpkg.enpkg_studio import enpkga_builder
from app.core.agents.interpreter.interpreter_studio import ia_builder
from app.core.agents.sparql.sparql_studio import sparqla_builder


def router_entry(state) -> Literal["validator_agent", "supervisor_agent"]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return "validator_agent"


def router_validator(state) -> Literal["supervisor_agent", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END


def router_supervisor(
    state,
) -> Literal["enpkg_agent", "sparql_agent", "interpretor_agent", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the enpkg agent" in last_message.content:
        return "enpkg_agent"
    if "calling the sparql agent" in last_message.content:
        return "sparql_agent"
    if "calling the interpretor agent" in last_message.content:
        return "interpretor_agent"
    return END


def router_sparql(state) -> Literal["supervisor_agent", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END


def router_enpkg(state) -> Literal["supervisor_agent", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END


def router_interpretor(state) -> Literal["supervisor_agent", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END


kgbot_builder = StateGraph(MessagesState)
kgbot_builder.add_node("entry_agent", ea_builder.compile())
kgbot_builder.add_node("validator_agent", va_builder.compile())
kgbot_builder.add_node("supervisor_agent", sa_builder.compile())
kgbot_builder.add_node("enpkg_agent", enpkga_builder.compile())
kgbot_builder.add_node("sparql_agent", sparqla_builder.compile())
kgbot_builder.add_node("interpretor_agent", ia_builder.compile())


kgbot_builder.add_edge(START, "entry_agent")
kgbot_builder.add_conditional_edges("entry_agent", router_entry)
kgbot_builder.add_conditional_edges("validator_agent", router_validator)
kgbot_builder.add_conditional_edges("supervisor_agent", router_supervisor)
kgbot_builder.add_conditional_edges("enpkg_agent", router_enpkg)
kgbot_builder.add_conditional_edges("sparql_agent", router_sparql)
kgbot_builder.add_conditional_edges("interpretor_agent", router_interpretor)

memory = MemorySaver()
graph = kgbot_builder.compile(checkpointer=memory)
