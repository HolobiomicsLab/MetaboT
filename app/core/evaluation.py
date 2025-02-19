from dotenv import load_dotenv
import os
from langsmith import Client
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph
from app.core.workflow.langraph_workflow import create_workflow
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain.evaluation import EvaluatorType
from langsmith.schemas import Example, Run
from langchain.smith import run_on_dataset, RunEvalConfig
from langchain.evaluation import load_evaluator
from uuid import uuid4
from app.core.utils import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = (
    os.environ.get("LANGCHAIN_PROJECT")
    or os.environ.get("LANGSMITH_PROJECT")
    or "MetaboT evaluation"
)
os.environ["LANGCHAIN_ENDPOINT"] = (
    os.environ.get("LANGCHAIN_ENDPOINT")
    or os.environ.get("LANGSMITH_ENDPOINT")
    or os.environ.get("LANGSMITH_BASE_URL")
    or "https://api.smith.langchain.com"
)

# Initialize Langsmith client
api_key = os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")
if not api_key:
    raise ValueError("The environment variable LANGCHAIN_API_KEY is not defined")

client = Client(api_key=api_key)

# Dataset configuration
dataset_name = "smaller_benchmark_temporal"

# Custom criteria for SPARQL query evaluation
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

    # Create workflow in evaluation mode
workflow = create_workflow(
    api_key=os.getenv("OPENAI_API_KEY"),    
    evaluation=True
)

def evaluate_result(_input, thread_id: int = 1):
    """
    Evaluate the result based on input and thread ID.
    
    Args:
        _input (dict): Input containing messages to process
        thread_id (int): Thread identifier for the evaluation
        
    Returns:
        dict: The evaluation result
    """
    
    # Prepare the message
    message = {
        "messages": [
            HumanMessage(content=_input["messages"][0]["content"])
        ]
    }
    
    # Process the message through the workflow
    response = workflow.invoke(
        message,
        {"configurable": {"thread_id": thread_id}},
    )
    
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


