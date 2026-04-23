import os
import pandas as pd
import json

from uuid import uuid4
from dotenv import load_dotenv

from langsmith import Client
from langchain_core.messages import HumanMessage
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain.evaluation import EvaluatorType, load_evaluator
from langchain.smith import run_on_dataset, RunEvalConfig

from app.core.workflow.langraph_workflow import create_workflow
from app.core.main import llm_creation
from app.core.utils import setup_logger

# 1. Load environment variables
load_dotenv()
logger = setup_logger(__name__)

# 2. Check for required API keys safely
api_key = os.getenv("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Missing LANGCHAIN_API_KEY. Please copy .env.template to .env and add your key.")
if not openai_key:
    raise ValueError("Missing OPENAI_API_KEY. Please copy .env.template to .env and add your key.")

# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "MetaboT evaluation")
os.environ["LANGCHAIN_ENDPOINT"] = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.dirname(current_dir)
app_dir = os.path.dirname(core_dir)
local_data_path = os.path.join(app_dir, "data", "big_benchmark.csv")
client = Client(api_key=api_key)

dataset_name = "test_metabot"
# Check if the dataset exists in the current user's workspace
try:
    client.read_dataset(dataset_name=dataset_name)
    logger.info(f"Dataset '{dataset_name}' found in LangSmith workspace.")
except Exception:
    logger.info(f"Dataset '{dataset_name}' not found. Attempting to create it from local file...")


    if not os.path.exists(local_data_path):
        raise FileNotFoundError(
            f"Could not find '{local_data_path}'. Ensure the local dataset file is shared alongside this script.")


    # Load local data and create the dataset in the user's LangSmith account
    df = pd.read_csv(local_data_path)
    dataset = client.create_dataset(dataset_name=dataset_name, description="MetaboT  Benchmark")

    inputs = []
    outputs = []

    for _, row in df.iterrows():
        try:
            # The CSV stores the JSON arrays as strings, so we need to parse them back into Python objects
            parsed_messages = json.loads(row["messages"])
            parsed_end_state = json.loads(row["__end__"])

            inputs.append({"messages": parsed_messages})
            outputs.append({"__end__": parsed_end_state})

        except json.JSONDecodeError as e:
            logger.warning(f"Skipping a row due to JSON parsing error: {e}")
            continue

    client.create_examples(inputs=inputs, outputs=outputs, dataset_id=dataset.id)
    logger.info(f"Successfully created dataset '{dataset_name}' in LangSmith.")
# Custom criteria for SPARQL query evaluation
custom_criteria = {
    "structural similarity of SPARQL queries":
        "How similar is the structure of the generated SPARQL query to the reference SPARQL query? Does the generated query correctly match subjects to their corresponding objects as in the reference query"
}

eval_chain_new = load_evaluator(EvaluatorType.LABELED_CRITERIA, criteria=custom_criteria)

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

endpoint_url = os.environ.get("KG_ENDPOINT_URL", "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG")

models = llm_creation()

# Create workflow in evaluation mode
app = create_workflow(
    models=models,
    endpoint_url=endpoint_url,
    evaluation=True,
    api_key=openai_key
)


def evaluate_result(_input, thread_id: int = 1):
    """Evaluate the result based on input."""
    # Note: Adjust the 'question' key below if your dataset uses a different input key
    input_text = _input.get("question") or _input["messages"][0]["content"]

    message = {
        "messages": [HumanMessage(content=input_text)]
    }

    response = app.invoke(message, {"configurable": {"thread_id": thread_id}})
    return {"output": response}


unique_id = uuid4().hex[0:8]

# Run evaluation
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

logger.info(f"Evaluation complete. View results in LangSmith under project: Testing the app-{unique_id}")