from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

from app.core.agents.interpreter.tool_interpreter import Interpreter
from app.core.agents.interpreter.prompt import PROMPT
from app.core.utils import create_user_session



session_id = create_user_session()

it = Interpreter(None,None)
tools_interpretor_agent = [it]
llm = ChatOllama(model="llama3.2")
llm_with_tools = llm.bind_tools(tools_interpretor_agent)
# System message
sys_msg = SystemMessage(content= PROMPT     )

def interpretor_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

ia_builder = StateGraph(MessagesState)
ia_builder.add_node("interpretor_agent", interpretor_agent)
ia_builder.add_node("tools", ToolNode(tools_interpretor_agent))
ia_builder.add_edge(START, "interpretor_agent")
ia_builder.add_conditional_edges("interpretor_agent",tools_condition)
ia_builder.add_edge("tools", "interpretor_agent")



memory = MemorySaver()
graph = ia_builder.compile(checkpointer=memory)