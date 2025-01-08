from langchain_ollama import ChatOllama
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import tools_condition,ToolNode

from app.core.agents.sparql.tool_merge_result import OutputMerger
from app.core.agents.sparql.tool_sparql import GraphSparqlQAChain
from app.core.agents.sparql.tool_wikidata_query import WikidataStructureSearch
from app.core.agents.sparql.prompt import PROMPT
from app.core.utils import create_user_session



session_id = create_user_session()
llm = ChatOllama(model="llama3.2")

om = OutputMerger(None)
gqac = GraphSparqlQAChain(llm=llm,graph=None,session_id=None)
wss = WikidataStructureSearch(None)
tools_sparql_agent = [om,gqac,wss]
llm_with_tools = llm.bind_tools(tools_sparql_agent)
# System message
sys_msg = SystemMessage(content= PROMPT     )

# Node
def sparql_agent(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

sparqla_builder = StateGraph(MessagesState)
sparqla_builder.add_node("sparql_agent", sparql_agent)
sparqla_builder.add_node("tools", ToolNode(tools_sparql_agent))
sparqla_builder.add_edge(START, "sparql_agent")
sparqla_builder.add_conditional_edges("sparql_agent",tools_condition)
sparqla_builder.add_edge("tools", "sparql_agent")

memory = MemorySaver()
graph = sparqla_builder.compile(checkpointer=memory)