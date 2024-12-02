from dotenv import load_dotenv


import os
from langsmith import Client
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph
from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.agents.agents_factory import create_all_agents
from app.core.main import link_kg_database
from app.core.main import llm_creation
from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain.evaluation import EvaluatorType
from langsmith.schemas import Example, Run
from langchain.smith import run_on_dataset, RunEvalConfig
from langchain.evaluation import load_evaluator
from uuid import uuid4

# Load environment variables
load_dotenv()


# Set environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = (
        f"KGBot Testing - problematic queries"  # Please update the name here if you want to create a new project for separating the traces.
    )
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"


# Initialize Langsmith client
client = Client()

# Creating the datasets for testing
dataset_name = "Big Benchmark"

# custom criteria to evaluate sparql query
custom_criteria = {
    "structural similarity of SPARQL queries":
        "How similar is the structure of the generated SPARQL query to the reference SPARQL query? Does the generated query correctly match subjects to their corresponding objects as in the reference query"
}

# Load evaluator with custom criteria
eval_chain_new = load_evaluator(
    EvaluatorType.LABELED_CRITERIA,
    criteria=custom_criteria,
)


# Define the evaluation configuration
evaluation_config = RunEvalConfig(
    evaluators=[
        EvaluatorType.QA,
        RunEvalConfig.LabeledScoreString(
            {
                "accuracy": """
Score 1: The answer is completely unrelated to the reference.
Score 3: The answer has minor relevance but does not align with the reference.
Score 5: The answer has moderate relevance but contains inaccuracies.
Score 7: The answer aligns with the reference but has minor errors or omissions.
Score 10: The answer is completely accurate and aligns perfectly with the reference."""
            },
             normalize_by=10,
        ),
    ],

    custom_evaluators=[eval_chain_new],
)


# Link to the knowledge graph database and initialize models and agents
endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
graph = link_kg_database(endpoint_url)
models = llm_creation()
agents = create_all_agents(models, graph)
app = create_workflow(agents)

def evaluate_result(_input, thread_id: int = 1):
    """Evaluate the result based on input and thread ID."""
    message = {
                "messages": [
                    HumanMessage(content=_input["messages"][0]["content"])
                ]
            }
    response = app.invoke(message, {
                "configurable": {"thread_id": thread_id}
            }, )
    return {"output": response}


# Generate a unique identifier for the project
unique_id = uuid4().hex[0:8]

# Run evaluation on the dataset
chain_results = run_on_dataset(
    dataset_name=dataset_name,
    llm_or_chain_factory=evaluate_result,
    evaluation=evaluation_config,
    verbose=True,
    project_name=f"Testing the app-{unique_id}",
    client=client,

 project_metadata={
         "model": "gpt-4o",
   },
)