from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode
from app.core.agents.supervisor.prompt import PROMPT

tools_supervisor_agent = []
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_supervisor_agent)
# System message
sys_msg = SystemMessage(content= PROMPT     )

# Node
def supervisor_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

sa_builder = StateGraph(MessagesState)
sa_builder.add_node("supervisor_agent", supervisor_agent)
sa_builder.add_node("tools", ToolNode(tools_supervisor_agent))
sa_builder.add_edge(START, "supervisor_agent")
sa_builder.add_conditional_edges("supervisor_agent",tools_condition)
sa_builder.add_edge("tools", "supervisor_agent")
memory = MemorySaver()
graph = sa_builder.compile(checkpointer=memory)