from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

from app.core.agents.validator.tool_validator import PlantDatabaseChecker
from app.core.agents.validator.prompt import PROMPT

pdc = PlantDatabaseChecker()
tools_validator_agent = [pdc]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_validator_agent)
# System message
sys_msg = SystemMessage(content= PROMPT     )

# Node
def validator_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

va_builder = StateGraph(MessagesState)
va_builder.add_node("validator_agent", validator_agent)
va_builder.add_node("tools", ToolNode(tools_validator_agent))
va_builder.add_edge(START, "validator_agent")
va_builder.add_conditional_edges("validator_agent",tools_condition)
va_builder.add_edge("tools", "validator_agent")

memory = MemorySaver()
graph = va_builder.compile(checkpointer=memory)