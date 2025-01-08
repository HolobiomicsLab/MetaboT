from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

def summaries(state):
    """ Summaries a Text """
    return {"messages": ["The Entry Agent : Summaries the Text"]}

tools_entry_agent = [summaries]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_entry_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def entry_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

ea_builder = StateGraph(MessagesState)
ea_builder.add_node("entry_agent", entry_agent)
ea_builder.add_node("tools", ToolNode(tools_entry_agent))
ea_builder.add_edge(START, "entry_agent")
ea_builder.add_conditional_edges("entry_agent",tools_condition)
ea_builder.add_edge("tools", "entry_agent")

# ## Validator Agent

def validate(state):
    """ Validate a Text """
    return {"messages": ["Validator agent: Query validated"]}


tools_validator_agent = [summaries]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_validator_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def validator_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


va_builder = StateGraph(MessagesState)
va_builder.add_node("validator_agent", validator_agent)
va_builder.add_node("tools", ToolNode(tools_validator_agent))
va_builder.add_edge(START, "validator_agent")
va_builder.add_conditional_edges("validator_agent",tools_condition)
va_builder.add_edge("tools", "validator_agent")

# ## Supervisor Agent

def supervise(state):
    """ Supervisor a Text """
    return {"messages": ["Supervisor agent: Query validated"]}


tools_supervisor_agent = [supervise]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_supervisor_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def supervisor_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

sa_builder = StateGraph(MessagesState)
sa_builder.add_node("supervisor_agent", supervisor_agent)
sa_builder.add_node("tools", ToolNode(tools_supervisor_agent))
sa_builder.add_edge(START, "supervisor_agent")
sa_builder.add_conditional_edges("supervisor_agent",tools_condition)
sa_builder.add_edge("tools", "supervisor_agent")

# ## ENPKG Agent

def do_stuff(state):
    """ Validate a Text """
    return {"messages": ["Validator agent: Query validated"]}


tools_enpkg_agent = [do_stuff]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_enpkg_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def enpkg_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

enpkga_builder = StateGraph(MessagesState)
enpkga_builder.add_node("enpkg_agent", enpkg_agent)
enpkga_builder.add_node("tools", ToolNode(tools_enpkg_agent))
enpkga_builder.add_edge(START, "enpkg_agent")
enpkga_builder.add_conditional_edges("enpkg_agent",tools_condition)
enpkga_builder.add_edge("tools", "enpkg_agent")

# ## SPARQL Agent

def run_query(state):
    """ Validate a Text """
    return {"messages": ["Validator agent: Query validated"]}


tools_sparql_agent = [run_query]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_sparql_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def sparql_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

sparqla_builder = StateGraph(MessagesState)
sparqla_builder.add_node("sparql_agent", sparql_agent)
sparqla_builder.add_node("tools", ToolNode(tools_sparql_agent))
sparqla_builder.add_edge(START, "sparql_agent")
sparqla_builder.add_conditional_edges("sparql_agent",tools_condition)
sparqla_builder.add_edge("tools", "sparql_agent")


# ## Interpreter Agent

def interpret(state):
    """ Interpret a Text """
    return {"messages": ["Validator agent: Query validated"]}


tools_interpretor_agent = [interpret]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_interpretor_agent)

# System message
sys_msg = SystemMessage(content= "")

# Node
def interpretor_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

ia_builder = StateGraph(MessagesState)
ia_builder.add_node("interpretor_agent", interpretor_agent)
ia_builder.add_node("tools", ToolNode(tools_interpretor_agent))
ia_builder.add_edge(START, "interpretor_agent")
ia_builder.add_conditional_edges("interpretor_agent",tools_condition)
ia_builder.add_edge("tools", "interpretor_agent")


def router_entry(state)-> Literal["validator_agent",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the validator agent" in last_message.content:
        return "validator_agent"
    return END

def router_validator(state)-> Literal["supervisor_agent",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END

def router_supervisor(state)-> Literal["enpkg_agent","sparql_agent","interpretor_agent",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the enpkg agent" in last_message.content:
        return "enpkg_agent"
    if "calling the sparql agent" in last_message.content:
        return "sparql_agent"
    if "calling the interpretor agent" in last_message.content:
        return "interpretor_agent"
    return END

def router_sparql(state)-> Literal["supervisor_agent",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END

def router_enpkg(state)-> Literal["supervisor_agent",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if "calling the supervisor agent" in last_message.content:
        return "supervisor_agent"
    return END

def router_interpretor(state)-> Literal["supervisor_agent",END]:
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
