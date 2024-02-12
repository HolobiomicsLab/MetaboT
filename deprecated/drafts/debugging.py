# from tools_script import SparqlTool, DBRetriever, count_tokens, SimpleAgent
from enpkg_agent import run_agent
from enpkg_tools import make_toolset
import os




if __name__ == '__main__':
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    endpoint_url = 'https://enpkg.commons-lab.org/graphdb/repositories/ENPKG'


    q3 = 'Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?'


    tools = make_toolset(endpoint_url=endpoint_url)
    
    run_agent(q3, tools)