from app.core.agents.agents_factory import create_all_agents
from app.core.main import langsmith_setup, link_kg_database
from app.core.main import llm_creation
from app.core.workflow.langraph_workflow import create_workflow

# Link to the knowledge graph database and initialize models and agents
# langsmith_setup()
endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
graph = link_kg_database(endpoint_url)
models = llm_creation()
agents = create_all_agents(models, graph)
app = create_workflow(agents)

# Test with the following question
# Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count of features as aspidosperma-type alkaloids?