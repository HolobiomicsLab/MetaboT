from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

from app.core.agents.enpkg.tool_chemicals import ChemicalResolver
from app.core.agents.enpkg.tool_smiles import SMILESResolver
from app.core.agents.enpkg.tool_target import TargetResolver
from app.core.agents.enpkg.tool_taxon import TaxonResolver
from app.core.agents.enpkg.prompt import PROMPT

cr = ChemicalResolver()
sr = SMILESResolver()
tar = TargetResolver()
txr = TaxonResolver()

tools_enpkg_agent = [cr,sr,tar,txr]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_enpkg_agent)
# System message
sys_msg = SystemMessage(content=PROMPT)

# Node
def enpkg_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

enpkga_builder = StateGraph(MessagesState)
enpkga_builder.add_node("enpkg_agent", enpkg_agent)
enpkga_builder.add_node("tools", ToolNode(tools_enpkg_agent))
enpkga_builder.add_edge(START, "enpkg_agent")
enpkga_builder.add_conditional_edges("enpkg_agent",tools_condition)
enpkga_builder.add_edge("tools", "enpkg_agent")


memory = MemorySaver()
graph = enpkga_builder.compile(checkpointer=memory)