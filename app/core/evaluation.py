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
from uuid import uuid4
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = (
        f"KGBot Testing - problematic queries"  # Please update the name here if you want to create a new project for separating the traces.
    )
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

client = Client()
dataset_inputs = [
    "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?",
    "Which samples have features (positive ionization mode) annotated as aspidosperma-type alkaloids by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids?",
    "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode which are also reported in the Tabernaemontana genus in Wikidata.",
    "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm).",
    #"Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- adduct (+/- 5ppm)."
   #"Among the structural annotations from Tabernaemontana coffeoides (Apocynaceae) seeds extract, which ones contain an aspidospermidine substructure?",
    #"Among the SIRIUS structural annotations from Tabernaemontana coffeoides (Apocynaceae) seeds extract, which ones are reported in the Tabernaemontana genus in WD?",
    #"Which compounds annotated in the active extract of Melochia umbellata have activity against T. cruzi reported (in ChEMBL), and in which taxon they are reported (in Wikidata)?",
    #"Filter the positive ionization mode features of Melochia umbellata annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in negative ionization mode is detected with the same retention time (± 3 seconds) and a mass corresponding to the [M-H]- adduct (± 5 ppm)",
    #"For features from Melochia umbellata in positive mode mode with SIRIUS annotations, get the ones for which a feature in negative ionization mode with the same retention time (± 3 sec) has the same SIRIUS annotation (2D IK)."
]

example_outputs = [
    "The number of features (in both positive and negative ionization modes) that have the same SIRIUS/CSI:FingerID and ISDB annotation, as determined by comparing the InCHIKey2D of the annotations, is 33,255.",
    "The extracts that have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids are:\\n\\n1. Extract [VGF152_B02](https://enpkg.commons-lab.org/kg/VGF152_B02) with 74 features.\\n2. Extract [VGF157_D02](https://enpkg.commons-lab.org/kg/VGF157_D02) with 11 features.\\n3. Extract [VGF147_B11](https://enpkg.commons-lab.org/kg/VGF147_B11) with 10 features.\\n4. Extract [VGF153_C03](https://enpkg.commons-lab.org/kg/VGF153_C03) with 7 features.\\n5. Extract [VGF157_E02](https://enpkg.commons-lab.org/kg/VGF157_E02) with 2 features.\\n6. Extract [VGF154_D02](https://enpkg.commons-lab.org/kg/VGF154_D02) with 2 features.\\n7. Extract [VGF147_A10](https://enpkg.commons-lab.org/kg/VGF147_A10) with 2 features.\\n8. Extract [VGF140_F02](https://enpkg.commons-lab.org/kg/VGF140_F02) with 2 features.\\n9. And several other extracts with 1 feature each",
    "The answer to the question is the dataset with Wikidata IDs of chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode and reported in the Tabernaemontana genus in Wikidata. The SPARQL query generated to answer to this question is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\nPREFIX ns2: <https://enpkg.commons-lab.org/module/>\nPREFIX wd: <http://www.wikidata.org/entity/>\n\nSELECT DISTINCT ?wikidataID\nWHERE {\n    ?rawMaterial ns1:has_wd_id wd:Q15376858 .\n    ?rawMaterial ns1:has_lab_process ?labExtract .\n    ?labExtract ns1:has_LCMS ?lcmsAnalysis .\n    ?lcmsAnalysis ns1:has_lcms_feature_list ?featureList .\n    ?featureList ns1:has_lcms_feature ?feature .\n    ?feature ns1:has_sirius_annotation ?siriusAnnotation .\n    ?siriusAnnotation ns1:has_InChIkey2D ?inchiKey2D .\n    ?inchiKey2D ns1:is_InChIkey2D_of ?chemicalEntity .\n    ?chemicalEntity ns1:has_wd_id ?wikidataID .\n}",
    "The pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS have been filtered to retain only those for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- sirius adduct (+/- 5ppm). The SPARQL query generated for this question is: PREFIX ns1: <https://enpkg.commons-lab.org/kg/>\n  PREFIX ns2: <https://enpkg.commons-lab.org/module/>\n\n  SELECT ?posFeature ?negFeature\n  WHERE {\n      ?rawMaterial ns1:has_wd_id <http://www.wikidata.org/entity/Q6813281> .\n      ?rawMaterial ns1:has_lab_process ?labExtract .\n      ?labExtract ns1:has_LCMS ?posAnalysis .\n      ?posAnalysis a ns1:LCMSAnalysisPos .\n      ?posAnalysis ns1:has_lcms_feature_list ?posFeatureList .\n      ?posFeatureList ns1:has_lcms_feature ?posFeature .\n      ?posFeature ns1:has_sirius_annotation ?posAnnotation .\n      ?posAnnotation ns1:has_sirius_adduct \"[M+H]+\" .\n      ?posFeature ns1:has_retention_time ?posRT .\n      ?posFeature ns1:has_parent_mass ?posMass .\n\n      ?labExtract ns1:has_LCMS ?negAnalysis .\n      ?negAnalysis a ns1:LCMSAnalysisNeg .\n      ?negAnalysis ns1:has_lcms_feature_list ?negFeatureList .\n      ?negFeatureList ns1:has_lcms_feature ?negFeature .\n      ?negFeature ns1:has_sirius_annotation ?negAnnotation .\n      ?negAnnotation ns1:has_sirius_adduct \"[M-H]-\" .\n      ?negFeature ns1:has_retention_time ?negRT .\n      ?negFeature ns1:has_parent_mass ?negMass .\n\n      FILTER (ABS(?posRT - ?negRT) <= 3)\n      FILTER (ABS(?posMass - ?negMass) / ?posMass <= 0.000005)\n  }",
    #"The SPARQL query generated is: PREFIX ns1: <https://enpkg.commons-lab.org/module/>\nPREFIX ns2: <https://enpkg.commons-lab.org/kg/>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n\nSELECT ?posFeature ?negFeature\nWHERE {\n    ?taxon ns2:has_wd_id <http://www.wikidata.org/entity/Q6813281> .\n    ?taxon ns2:has_lab_process ?extract .\n    ?extract ns2:has_LCMS ?posAnalysis .\n    ?extract ns2:has_LCMS ?negAnalysis .\n    ?posAnalysis a ns2:LCMSAnalysisPos .\n    ?negAnalysis a ns2:LCMSAnalysisNeg .\n    ?posAnalysis ns2:has_lcms_feature_list ?posFeatureList .\n    ?negAnalysis ns2:has_lcms_feature_list ?negFeatureList .\n    ?posFeatureList ns2:has_lcms_feature ?posFeature .\n    ?negFeatureList ns2:has_lcms_feature ?negFeature .\n    ?posFeature ns2:has_sirius_annotation ?posAnnotation .\n    ?posAnnotation ns2:has_sirius_adduct "[M+H]+" .\n    ?posFeature ns2:has_retention_time ?posRetentionTime .\n    ?posFeature ns2:has_parent_mass ?posMass .\n    ?negFeature ns2:has_retention_time ?negRetentionTime .\n    ?negFeature ns2:has_parent_mass ?negMass .\n    FILTER (abs(?posRetentionTime - ?negRetentionTime) <= 3) .\n    FILTER (abs(?posMass - ?negMass) / ?posMass <= 5e-6) .\n} "

    #"3 distinct stereochemically undefined structures (2D InChiKey) that contain an aspidospermidine substructure: COC(=O)C1=C2Nc3ccccc3C23CCN2CC4(CC5CC67CC(=O)OC6CCN6CCC8(c9cccc(OC)c9N(C4)C58O)C67)C4OCCC4(C1)C23, COC(=O)C1CC23CCC[N+]4(C2C5(C1(CC3)NC6=CC=CC=C65)CC4)[O-], COC(=O)C1=C2Nc3ccccc3C23CCN2C3C3(CCOC3C3CC4CC56CCOC5CCN5CCC7(c8cccc(OC)c8NC47C32)C56)C1.",
    #"18 distinct stereochemically undefined structures annotated by SIRIUS in Tabernaemontana coffeoides (Apocynaceae) seeds extract and reported in at least one Tabernaemontana sp.",
    #"14 distinct stereochemically undefined structures, all of them reported in Waltheria indica.",
    #"62 features from Melochia umbellata in positive ionization mode annotated as [M+H]+ by SIRIUS with their corresponding potential [M-H]"
    #"22 features in positive ionization mode for which a feature in negative ionization mode with the same retention time has the same annotation."
]



# Creating the datasets for testing
dataset_name = "Testing_gpt_4o_version_2"
dataset = client.create_dataset(
    dataset_name,
    description="An example dataset of questions to run",
)

client.create_examples(
    inputs=[{"question": question} for question in dataset_inputs],
    outputs=[{"output": answer} for answer in example_outputs],
    dataset_id=dataset.id,
)


@run_evaluator
def check_not_idk(run: Run, example: Example):
    """Illustration of a custom evaluator."""
    agent_response = run.outputs["output"]
    if "don't know" in agent_response or "not sure" in agent_response:
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

        # You can select a default one such as "helpfulness" or provide your own.
        RunEvalConfig.LabeledCriteria("helpfulness"),
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
    custom_evaluators=[check_not_idk],
)



endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
graph = link_kg_database(endpoint_url)
models = llm_creation()
agents = create_all_agents(models, graph)
app = create_workflow(agents)
def evaluate_result(_input, thread_id: int = 1):
    message = {
                "messages": [
                    HumanMessage(content=_input["question"])
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