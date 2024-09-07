from dotenv import load_dotenv
load_dotenv()

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

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = (
        f"KGBot Testing - problematic queries"  # Please update the name here if you want to create a new project for separating the traces.
    )
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

client = Client()
dataset_inputs = [
    # "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?",
    # "Which samples have features (positive ionization mode) annotated as aspidosperma-type alkaloids by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids?",
    # "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode which are also reported in the Tabernaemontana genus in Wikidata.",
    "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm).",
    # "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D.",
    # "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?",
    # "What are all distinct submitted taxons for the extracts?",
]

example_outputs = [
    # "The number of features (in both positive and negative ionization modes) that have the same SIRIUS/CSI:FingerID and ISDB annotation, as determined by comparing the InCHIKey2D of the annotations, is 33,255.",
    # "The extracts that have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids are:\\n\\n1. Extract [VGF152_B02](https://enpkg.commons-lab.org/kg/VGF152_B02) with 74 features.\\n2. Extract [VGF157_D02](https://enpkg.commons-lab.org/kg/VGF157_D02) with 11 features.\\n3. Extract [VGF147_B11](https://enpkg.commons-lab.org/kg/VGF147_B11) with 10 features.\\n4. Extract [VGF153_C03](https://enpkg.commons-lab.org/kg/VGF153_C03) with 7 features.\\n5. Extract [VGF157_E02](https://enpkg.commons-lab.org/kg/VGF157_E02) with 2 features.\\n6. Extract [VGF154_D02](https://enpkg.commons-lab.org/kg/VGF154_D02) with 2 features.\\n7. Extract [VGF147_A10](https://enpkg.commons-lab.org/kg/VGF147_A10) with 2 features.\\n8. Extract [VGF140_F02](https://enpkg.commons-lab.org/kg/VGF140_F02) with 2 features.\\n9. And several other extracts with 1 feature each",
    # "The answer to the question is the dataset with Wikidata IDs of chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode and reported in the Tabernaemontana genus in Wikidata. The SPARQL query generated to answer to this question is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\nPREFIX ns2: <https://enpkg.commons-lab.org/module/>\nPREFIX wd: <http://www.wikidata.org/entity/>\n\nSELECT DISTINCT ?wikidataID\nWHERE {\n    ?rawMaterial ns1:has_wd_id wd:Q15376858 .\n    ?rawMaterial ns1:has_lab_process ?labExtract .\n    ?labExtract ns1:has_LCMS ?lcmsAnalysis .\n    ?lcmsAnalysis ns1:has_lcms_feature_list ?featureList .\n    ?featureList ns1:has_lcms_feature ?feature .\n    ?feature ns1:has_sirius_annotation ?siriusAnnotation .\n    ?siriusAnnotation ns1:has_InChIkey2D ?inchiKey2D .\n    ?inchiKey2D ns1:is_InChIkey2D_of ?chemicalEntity .\n    ?chemicalEntity ns1:has_wd_id ?wikidataID .\n}",
    "The pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS have been filtered to retain only those for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- sirius adduct (+/- 5ppm). The SPARQL query generated for this question is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\n  PREFIX ns2: <https://enpkg.commons-lab.org/module/>\n\n  SELECT ?posFeature ?negFeature\n  WHERE {\n      ?rawMaterial ns1:has_wd_id <http://www.wikidata.org/entity/Q6813281> .\n      ?rawMaterial ns1:has_lab_process ?labExtract .\n      ?labExtract ns1:has_LCMS ?posAnalysis .\n      ?posAnalysis a ns1:LCMSAnalysisPos .\n      ?posAnalysis ns1:has_lcms_feature_list ?posFeatureList .\n      ?posFeatureList ns1:has_lcms_feature ?posFeature .\n      ?posFeature ns1:has_sirius_annotation ?posAnnotation .\n      ?posAnnotation ns1:has_sirius_adduct \"[M+H]+\" .\n      ?posFeature ns1:has_retention_time ?posRT .\n      ?posFeature ns1:has_parent_mass ?posMass .\n\n      ?labExtract ns1:has_LCMS ?negAnalysis .\n      ?negAnalysis a ns1:LCMSAnalysisNeg .\n      ?negAnalysis ns1:has_lcms_feature_list ?negFeatureList .\n      ?negFeatureList ns1:has_lcms_feature ?negFeature .\n      ?negFeature ns1:has_sirius_annotation ?negAnnotation .\n      ?negAnnotation ns1:has_sirius_adduct \"[M-H]-\" .\n      ?negFeature ns1:has_retention_time ?negRT .\n      ?negFeature ns1:has_parent_mass ?negMass .\n\n      FILTER (ABS(?posRT - ?negRT) <= 3)\n      FILTER (ABS(?posMass - ?negMass) / ?posMass <= 0.000005)\n  }",
    # "The answer to this question are the features for which a feature in negative ionization mode with the same retention time has the same annotation. The SPARQL query geenrated: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\nPREFIX ns2: <https://enpkg.commons-lab.org/module/>\nPREFIX wd: <http://www.wikidata.org/entity/>\n\nSELECT ?featurePos ?retentionTimePos ?InChIkey2D\nWHERE {\n    ?rawMaterial ns1:has_wd_id wd:Q6813281 .\n    ?rawMaterial ns1:has_lab_process ?labExtract .\n    ?labExtract ns1:has_LCMS ?analysisPos .\n    ?analysisPos a ns1:LCMSAnalysisPos .\n    ?analysisPos ns1:has_lcms_feature_list ?featureListPos .\n    ?featureListPos ns1:has_lcms_feature ?featurePos .\n    ?featurePos ns1:has_retention_time ?retentionTimePos .\n    ?featurePos ns1:has_sirius_annotation ?siriusAnnotationPos .\n    ?siriusAnnotationPos ns1:has_InChIkey2D ?InChIkey2D .\n    ?labExtract ns1:has_LCMS ?analysisNeg .\n    ?analysisNeg a ns1:LCMSAnalysisNeg .\n    ?analysisNeg ns1:has_lcms_feature_list ?featureListNeg .\n    ?featureListNeg ns1:has_lcms_feature ?featureNeg .\n    ?featureNeg ns1:has_retention_time ?retentionTimeNeg .\n    ?featureNeg ns1:has_sirius_annotation ?siriusAnnotationNeg .\n    ?siriusAnnotationNeg ns1:has_InChIkey2D ?InChIkey2D .\n    FILTER (ABS(?retentionTimePos - ?retentionTimeNeg) <= 3)\n}",
    # "The count of features annotated as 'Tetraketide meroterpenoids' for each taxon and extract is provided, the SPARQL query generated is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\nPREFIX ns2: <https://enpkg.commons-lab.org/module/>\n\nSELECT ?submittedTaxon ?extract (COUNT(?feature) AS ?featureCount)\nWHERE {\n    ?feature ns1:has_canopus_annotation ?annotation .\n    ?annotation ns1:has_canopus_npc_class <https://enpkg.commons-lab.org/kg/npc_Tetraketide_meroterpenoids> .\n    ?featureList ns1:has_lcms_feature ?feature .\n    ?analysis ns1",
    # "The list of submitted taxons is provided, the SPARQL query generated is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\nPREFIX ns2: <https://enpkg.commons-lab.org/module/>\n\nSELECT DISTINCT ?submittedTaxon\nWHERE {\n    ?extract a ns1:LabExtract .\n    ?rawMaterial ns1:has_lab_process ?extract .\n    ?rawMaterial ns1:submitted_taxon ?submittedTaxon .\n}",



]



# Creating the datasets for testing
dataset_name = "Testing_new_evaluator30.08"
# dataset = client.create_dataset(
#     dataset_name,
#     description="An example dataset of questions to run",
# )
#
# client.create_examples(
#     inputs=[{"question": question} for question in dataset_inputs],
#     outputs=[{"output": answer} for answer in example_outputs],
#     dataset_id=dataset.id,
# )

# custom criteria to evaluate sparql query
custom_criteria = {
    "structural similarity of SPARQL queries": "How similar is the structure of the generated SPARQL query to the reference SPARQL query? Does the generated query correctly match subjects to their corresponding objects as in the reference query"
}

custom_criteria_2 = {
    "syntax validation": "Is the generated SPARQL query syntactically valid? "
}
eval_chain_new = load_evaluator(
    EvaluatorType.LABELED_CRITERIA,
    criteria=custom_criteria,
)

eval_chain_new_2= load_evaluator(
    EvaluatorType.CRITERIA,
    criteria=custom_criteria_2,
)
@run_evaluator
def check_not_idk(run: Run, example: Example):
    """Illustration of a custom evaluator."""
    agent_response = run.outputs["output"]
    if "don't know" in agent_response or "no results" in agent_response:
        score = 0
    else:
        score = 1
    # You can access the dataset labels in example.outputs[key]
    # You can also access the model inputs in run.inputs[key]
    return EvaluationResult(
        key="not_uncertain",
        score=score,
    )


# Defining the proper evaluation

evaluation_config = RunEvalConfig(
    # Evaluators can either be an evaluator type (e.g., "qa", "criteria", "embedding_distance", etc.) or a configuration for that evaluator
    evaluators=[
        # Measures whether a QA response is "Correct", based on a reference answer
        # You can also select via the raw string "qa"
        EvaluatorType.QA,
        # trying new evaluator
        RunEvalConfig.LabeledCriteria("helpfulness"),
        # You can select a default one such as "helpfulness" or provide your own.

        # The LabeledScoreString evaluator outputs a score on a scale from 1-10.
        # You can use default criteria or write our own rubric
        RunEvalConfig.LabeledScoreString(
            {
                "accuracy": """
Score 1: The answer is completely unrelated to the reference.
Score 3: The answer has minor relevance but does not align with the reference.
Score 5: The answer has moderate relevance but contains inaccuracies.
Score 7: The answer aligns with the reference but has minor errors or omissions.
Score 10: The answer is completely accurate and aligns perfectly with the reference."""
            },
            # normalize_by=10,
        ),
    ],
    # You can add custom StringEvaluator or RunEvaluator objects here as well, which will automatically be
    # applied to each prediction. Check out the docs for examples.
    custom_evaluators=[eval_chain_new],
)



endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
graph = link_kg_database(endpoint_url)
models = llm_creation()
agents = create_all_agents(models, graph)
app = create_workflow(agents)
# def evaluate_result(_input, thread_id: int = 1):
#     message = {
#                 "messages": [
#                     HumanMessage(content=_input["question"])
#                 ]
#             }
#     response = app.invoke(message, {
#                 "configurable": {"thread_id": thread_id}
#             }, )
#     return {"output": response}

# trying to  evaluate based on run
def evaluate_result(_input, thread_id: int = 1):
    message = {
                "messages": [
                    HumanMessage(content=_input["messages"][0]["content"])
                ]
            }
    response = app.invoke(message, {
                "configurable": {"thread_id": thread_id}
            }, )
    return {"output": response}


unique_id = uuid4().hex[0:8]

chain_results = run_on_dataset(
    dataset_name=dataset_name,
    llm_or_chain_factory=evaluate_result,
    evaluation=evaluation_config,
    verbose=True,
    project_name=f"Testing the app-{unique_id}",
    client=client,
    # Project metadata communicates the experiment parameters,
    # Useful for reviewing the test results
 project_metadata={
    #     "env": "testing-notebook",
         "model": "gpt-4o",
    #     "prompt": "5d466cbc",
 },
)