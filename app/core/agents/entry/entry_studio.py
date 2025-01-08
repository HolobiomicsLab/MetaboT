from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

from app.core.agents.entry.tool_filesparser import FileAnalyzer
from app.core.agents.entry.prompt import PROMPT
from app.core.utils import create_user_session



session_id = create_user_session()

fa = FileAnalyzer(session_id=session_id)
tools_entry_agent = [fa]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_entry_agent)
# System message
sys_msg = SystemMessage(content= PROMPT     )

# Node
def entry_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

ea_builder = StateGraph(MessagesState)
ea_builder.add_node("entry_agent", entry_agent)
ea_builder.add_node("tools", ToolNode(tools_entry_agent))
ea_builder.add_edge(START, "entry_agent")
ea_builder.add_conditional_edges("entry_agent",tools_condition)
ea_builder.add_edge("tools", "entry_agent")

memory = MemorySaver()
graph = ea_builder.compile(checkpointer=memory)