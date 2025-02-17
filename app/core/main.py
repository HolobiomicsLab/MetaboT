import configparser
from pathlib import Path
import pickle
import os
from typing import Any
import functools
import argparse

from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

import os

from langsmith import Client
from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.agents.agents_factory import create_all_agents
from app.core.workflow.langraph_workflow import create_workflow, process_workflow, initiate_workflow, agent_node
from app.core.utils import setup_logger, load_config
from app.core.agents.agents_factory import create_all_agents
# libraries needed to check the endpoint
import requests
import certifi
logger = setup_logger(__name__)

parent_dir = Path(__file__).resolve().parent.parent
graph_path = parent_dir / "graphs" / "graph.pkl"
params_path = parent_dir / "config" / "params.ini"


def link_kg_database(endpoint_url: str):
    """
    Checks if an RDF graph is already created, and if not, it initializes and saves a new RDF graph object using a specified endpoint URL.

    Returns:
        RdfGraph: An RDF graph object.
    """

    # check if the graph is already created if not create it.
    try:
        with open(graph_path, "rb") as input_file:
            graph = pickle.load(input_file)
            # logger.info(f"schema: {graph.get_schema}")
            return graph
    except FileNotFoundError:
        pass

    # Initialize the RdfGraph object with the given endpoint and the standard set to 'rdf'
    graph = RdfGraph(query_endpoint=endpoint_url, standard="rdf")

    with open(graph_path, "wb") as output_file:
        pickle.dump(graph, output_file)
    # logger.info(f"schema: {graph.get_schema}")
    return graph


def get_deepseek_key():
    return os.getenv("DEEPSEEK_API_KEY")

def get_ovh_key():
    return os.getenv("OVHCLOUD_API_KEY")

def llm_creation(api_key=None):
    """
    Reads the parameters from the configuration file params.ini and initializes the language models.

    Args:
        api_key (str, optional): The API key for the OpenAI API.

    Returns:
        dict: A dictionary containing the language models.
    """

    config = configparser.ConfigParser()
    config.read(params_path)

    sections = ["llm", "llm_preview", "llm_o", "llm_mini", "llm_o3_mini", "llm_o1",
               "deepseek_deepseek-chat", "deepseek_deepseek-reasoner",
               "ovh_Meta-Llama-3_1-70B-Instruct"]
    models = {}

    # Get the OpenAI API key from the configuration file or the environment variables if none as passed. This allows Streamlit to pass the API key as an argument.
    openai_api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")

    for section in sections:
        temperature = config[section]["temperature"]
        model_id = config[section]["id"]
        max_retries = config[section]["max_retries"]
        
        if section.startswith("deepseek"):
            base_url = config[section]["base_url"]
            llm = ChatOpenAI(
                temperature=temperature,
                model=model_id,
                max_retries=max_retries,
                verbose=True,
                openai_api_base=base_url,
                openai_api_key=get_deepseek_key(),
            )
        elif section.startswith("ovh"):
            base_url = config[section]["base_url"]
            llm = ChatOpenAI(
                temperature=temperature,
                model=model_id,
                max_retries=max_retries,
                verbose=True,
                base_url=base_url,
                api_key=get_ovh_key(),
            )
        else:
            llm = ChatOpenAI(
                temperature=temperature,
                model=model_id,
                max_retries=max_retries,
                verbose=True,
                openai_api_key=openai_api_key,
            )
        models[section] = llm

    return models


def langsmith_setup():
    """
    Set up the LangSmith environment and client if an API key is present.
    If no API key is found, disable V2 tracing.
    """

    # Check whether an API key is present
    api_key = os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY")

    if not api_key:
        # If there's no API key, disable V2 tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        print("[LangSmith Setup] No API key found, LANGCHAIN_TRACING_V2 set to false.")
        return  # no further setup needed
    else:
        # If an API key exists, enable V2 tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        # Set default project if not already set
        os.environ["LANGCHAIN_PROJECT"] = (
            os.environ.get("LANGCHAIN_PROJECT")
            or os.environ.get("LANGSMITH_PROJECT")
            or "MetaboT"
        )

        # Set default endpoint if not already set
        os.environ["LANGCHAIN_ENDPOINT"] = (
            os.environ.get("LANGCHAIN_ENDPOINT")
            or os.environ.get("LANGSMITH_ENDPOINT")
            or os.environ.get("LANGSMITH_BASE_URL")
            or "https://api.smith.langchain.com"
        )

    try:
        client = Client(api_key=api_key)
        print(f"Langchain client was initialized: {client}")
    except Exception as e:
        print(f"Failed to initialize Langchain client: {e}")

def main():

    standard_questions = [
        "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?",
        "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count of features as aspidosperma-type alkaloids? Group by extract.",
        "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode which are also reported in the Tabernaemontana genus in Wikidata.",
        "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Trypanosoma cruzi target?",
        "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm). Provide the features and retention time.",
        "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D",
        "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?",
        "What are all distinct submitted taxons for the extracts of the Desmodium heterophyllum?",
        "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process",
        "What are the retention times, parent masses, and associated Spec2Vec peaks for features in the LC-MS analysis of the plant Rumex nepalensis in positive ion mode?",
        "How unique InChIKey2D are among the structural annotations?",
        "How many distinct Wikidata identifiers (WD IDs) have the same metabolite annotation (considering only the plannar structure)?",
        "Count the number of LCMS features in negative ionization mode",
        "Which molecules (represented by their InChIkey) have reported ChEMBL activity with activity type  IC50 and activity values below 500 nM against Leishmania donovani target?",
        "What are the mass spectrometry features detected for the plant Rumex nepalensis?",
        "What are the chemical structure ISDB annotations for Lovoa trichilioides ?",
        "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract?",
        "Can you provide the SMILES notation and the Wikidata IDs for the compound with the highest precursor ion mass in the MS2 spectra from extracts of Lovoa trichilioides by looking at SIRIUS annotations?",
        "What are the retention times and molecular masses of compounds identified in the negative ionization mode LCMS analysis from  Lovoa trichilioides extracts, and what are the CANOPUS chemical class annotations for those features?",
        "Which lab extracts from Melochia umbellata  yield compounds that, when analyzed in positive ionization mode LCMS, have a retention time of less than 2 minutes and demonstrate an inhibition percentage greater than 70% in bioassay results? Provide lab extracts, retention times and inhibition percentage.",
        "Which compounds from Desmodium heterophyllum extracts have annotations from both ISDB and SIRIUS, and what are their molecular masses?",
        "What is the distribution of chemical superclasses in the LCMS features annotated by CANOPUS identified from Desmodium heterophyllum extracts?",
        "What are the CANOPUS annotations for pairs of features from Desmodium heterophyllum extracts that share a cosine similarity score greater than 0.8? Provide the features and annotations for each feature.",
        "Which plant has extracts containing compounds that demonstrated inhibition rates above 50% against Trypanosoma cruzi and are above 800 Da in mass? Provide the lab extracts",
        "What are the SIRIUS structural annotations associated with the MS2 spectra from the lab extracts of Tabernaemontana coffeoides?",
        "List the bioassay results  at 10µg/mL against T.cruzi  for lab extracts of Tabernaemontana coffeoides.",
        "What are the most frequent SIRIUS chemical structure annotations (planar structure) observed from the extracts belonging to Hibiscus syriacus?",
        "Retrieve the Spec2Vec documents  associated with MS2 spectra  from the lab extracts  of Tabernaemontana coffeoides",
        "What are the ChEMBL targets (ChEMBLTarget) linked to ChEMBL assay results (ChEMBLAssayResults) for chemicals (ChEMBLChemical) sharing InChIKeys (InChIkey) with SIRIUS structural annotations (SiriusStructureAnnotation)?",
        "Retrieve the most frequent Spec2Vec peaks and losses characterizing the MS2 spectra from the lab extracts of Tabernaemontana coffeoides.",
        "Which lab extracts have bioassay results with inhibition percentages above 50% against Leishmania donovani target at 10 µg/mL?",
        "List the LC-MS features that have a chemical class annotation by CANOPUS and have a retention time between 5-7 minutes.",
        "Retrieve the lab extracts that have more than 2,000 features detected. ",
        "What are the LCMS features  that have feature areas  greater than 1,000,000 in positive ionization mode ?",
        "List the lab extracts  that have bioassay results  at  2µg/mL against Trypanosoma brucei rhodesiense .",
        "Which ChEMBL documents cited in ChEMBL assay results involve compounds (identified by InChIKeys) that are also observed in SIRIUS structural annotations within lab extracts, and which lab extracts contain the highest number of these shared compounds?",
        "For the LC-MS feature observed in the extracts of Tabernaemontana coffeoides, retrieve those that are annotated with a NPCPathways with CANOPUS.",
        "Retrieve the Wikidata IDs  of chemical entities  classified as Terpenoids in the lab extracts of Tabernaemontana coffeoides.",
        "Retrieve the Wikidata IDs of chemical entities from Desmodium heterophyllum that are annotated as rotenoids by CANOPUS and have ChEMBL assay results showing activity against Trypanosoma cruzi. Provide also the USIs to the corresponding MS/MS spectra.",
        "Retrieve the retention times and parent masses of LCMS features annotated as Terpenoids by CANOPUS in Tabernaemontana coffeoides.",
        "What are the most frequent adducts of LCMS features annotated by SIRIUS detected in positive ionization mode from Tabernaemontana coffeoides?",
        "What are the LCMS features with the highest area annotated as alkaloids by CANOPUS in Tabernaemontana coffeoides extracts?",
        "List the tissue types used to produce the lab extracts of Tabernaemontana coffeoides. Provide the tissue types  and lab extracts. ",
        "Which LCMS features from Tabernaemontana coffeoides have MS2 spectrum that have Spec2Vec peaks with values above 0.8? Provide MS2 spectra.",
        "What are the cosmic scores  and zodiac scores  associated with SIRIUS structural annotations  for LCMS features  from Tabernaemontana coffeoides?",
        "Retrieve the mass differences and cosine similarity scores for spectral pairs involving MS2 spectra from Desmodium heterophyllum.",
        "What are the LC-MS features that have GNPS library analogs annotation in Tabernaemontana coffeoides? Provide the features.",
        "Which ISDB annotations  have consistency scores  above 0.7 and taxonomic scores above 0.5 for LCMS features from Tabernaemontana coffeoides? Provide annotations.",
        "Retrieve the top-10 lab extracts with the most unique features detected (minimum feature area intensity of 500,000).",
        "What are the retention times and adduct types of LCMS features from Desmodium heterophyllum annotated by SIRIUS with a cosmic score greater than 0.4??",
        "Retrieve the top 5 tissues used to produce lab extracts that contain compounds with inhibition activity greater than 70% against Leishmania donovani target at 10 µg/mL.",
        "List the top 3 lab extracts with the highest number of unique compounds annotated by CANOPUS with a probability greater than 0.9.",
        "Which extracts have features (pos ionization mode) annotated as the class, isoquinoline-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count? Group by extract. ",
        "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode.",
        "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Leishmania donovani target?",
        "Which chemical compounds from Tabernaemontana coffeoides extract have the same SIRIUS and ISDB  annotations in positive and negative ionization mode? Provide the Inchikeys of 10 compounds. ",
        "Which chemical compounds demonstrated inhibition rates above 50% against Trypanosoma cruzi target? Provide the Inchikeys of 10 compounds. ",
        "Provide chemical compounds that have reported ChEMBL activity with activity type IC50 and activity values below 500 nM against Leishmania donovani target. Provide the Inchikeys of 10 compounds.",
        "Which chemical compounds have been observed both in ChEMBL documents and in SIRIUS structural annotations within lab extracts. Provide the Inchikeys of 10 compounds.",
        "Which chemical entities are classified as Terpenoids in the lab extracts of Tabernaemontana coffeoides? Provide the Inchikeys 10 compounds.",
        "Which chemical entities are annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability above 0.5? Provide the Inchikeys and corresponding Wikidata IDs of 10 chemical compounds.",
        "Retrieve the Inchikeys of chemical entities from Desmodium heterophyllum that are annotated as rotenoids by CANOPUS and have ChEMBL assay results showing activity against Trypanosoma cruzi. Provide 10 Inchikeys.",
        "Retrieve the Inchikeys and corresponding Wikidata IDs of chemical compounds with inhibition activity greater than 70% against Leishmania donovani target at 10 µg/mL. Restrict to 10 Inchikeys. ",
        "Which chemical entities from Melochia umbellata taxon in pos ionization mode have features annotated by SIRIUS? Provide 10 Inchikeys and corresponding Wikidata IDs.",
        "What are the InChIKeys and corresponding Wikidata IDs of chemical entities associated with LCMS features in positive ionization mode that have an ISDB annotation and a feature area greater than 1,000,000? List the top 10 results in descending order by feature area.",
        "Which chemical compounds detected in extracts of Desmodium heterophyllum are annotated as alkaloids in positive and negative ionization modes by SIRIUS? Provide the InChIKeys of 10 compounds.",
        "What are the chemical compounds with mass greater than 800 Da detected in LCMS features of Craterispermum laurinum? Provide the InChIKeys and molecular masses of the top 10 compounds.",
        "List the chemical compounds from Tabernaemontana coffeoides that have both ISDB and SIRIUS structural annotations matching a retention time of less than 5 minutes. Provide the InChIKeys and corresponding Wikidata IDs of 10 compounds.",
        "Which chemical compounds are detected in positive ionization mode from Tabernaemontana coffeoides? Provide the InChIKeys and corresponding Wikidata Ids of 10 compounds.",
        "What are the chemical compounds annotated by ISDB in extracts of Desmodium heterophyllum? Provide the InChIKeys  and corresponding Wikidata IDs of 10 compounds.",
        "What are the InChIKeys and their corresponding Wikidata IDs for chemical entities annotated by ISDB in the lab extracts of Desmodium heterophyllum?"
    ]

    parser = argparse.ArgumentParser(description="Process a workflow with a predefined or custom question.")
    parser.add_argument('-q', '--question', type=int, choices=range(1, (len(standard_questions))),
                        help=f"Choose a standard question number from 1 to {len(standard_questions)}.")
    parser.add_argument('-c', '--custom', type=str,
                        help="Provide a custom question.")

    args = parser.parse_args()

    if args.question:
        question = standard_questions[args.question - 1]
    elif args.custom:
        question = args.custom
    else:
        print("You must provide either a standard question number or a custom question.")
        return

    langsmith_setup()
    endpoint_url = os.environ.get("KG_ENDPOINT_URL") or "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"

    # endpoint_url = "https://enpkg.commons-lab.org/graphdb/sparql"
    graph = link_kg_database(endpoint_url)
    models = llm_creation()
    agents = create_all_agents(models, graph)
    workflow = create_workflow(agents, evaluation= False)

    # checking the endpoint
    # def check_knowledge_graph_endpoint(url):
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             print(f"The endpoint {url} is functional.")
    #         else:
    #             print(f"The endpoint {url} returned status code: {response.status_code}")
    #     except requests.exceptions.RequestException as e:
    #         print(f"An error occurred: {e}")
    #
    # check_knowledge_graph_endpoint(endpoint_url)
    q1 = "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?"
    q2 = "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count of features as aspidosperma-type alkaloids? Group by extract."
    q3 = "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode which are also reported in the Tabernaemontana genus in Wikidata."
    q4 = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Trypanosoma cruzi target?"
    q5 = "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm). Provide the features and retention time."
    q6 = "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D"
    q7 = "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?"
    q8 = "What are all distinct submitted taxons for the extracts of the Desmodium heterophyllum?"
    q9 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q10 = "What are the retention times, parent masses, and associated Spec2Vec peaks for features in the LC-MS analysis of the plant Rumex nepalensis in positive ion mode?"
    q11 = "How unique InChIKey2D are among the structural annotations?"
    q12 = "How many distinct Wikidata identifiers (WD IDs) have the same metabolite annotation (considering only the plannar structure)?"
    q13 = "Count the number of LCMS features in negative ionization mode"
    q14 = "Which molecules (represented by their InChIkey) have reported ChEMBL activity with activity type  IC50 and activity values below 500 nM against Leishmania donovani target?"
    q15 = "What are the mass spectrometry features detected for the plant Rumex nepalensis?"
    q16 = "What are the chemical structure ISDB annotations for Lovoa trichilioides ?"
    q24 = "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract?"
    q26 = "Can you provide the SMILES notation and the Wikidata IDs for the compound with the highest precursor ion mass in the MS2 spectra from extracts of Lovoa trichilioides by looking at SIRIUS annotations?"
    q27_modified = "What are the retention times and molecular masses of compounds identified in the negative ionization mode LCMS analysis from  Lovoa trichilioides extracts, and what are the CANOPUS chemical class annotations for those features?"
    q28 = "Which lab extracts from Melochia umbellata  yield compounds that, when analyzed in positive ionization mode LCMS, have a retention time of less than 2 minutes and demonstrate an inhibition percentage greater than 70% in bioassay results? Provide lab extracts, retention times and inhibition percentage."
    q29 = "Which compounds from Desmodium heterophyllum extracts have annotations from both ISDB and SIRIUS, and what are their molecular masses?"
    q30 = "What is the distribution of chemical superclasses in the LCMS features annotated by CANOPUS identified from Desmodium heterophyllum extracts?"
    q31 = "What are the CANOPUS annotations for pairs of features from Desmodium heterophyllum extracts that share a cosine similarity score greater than 0.8? Provide the features and annotations for each feature."
    q32_bis = "Which plant has extracts containing compounds that demonstrated inhibition rates above 50% against Trypanosoma cruzi and are above 800 Da in mass? Provide the lab extracts"
    q34 = "What are the SIRIUS structural annotations associated with the MS2 spectra from the lab extracts of Tabernaemontana coffeoides?"
    q37 = "List the bioassay results  at 10µg/mL against T.cruzi  for lab extracts of Tabernaemontana coffeoides."
    q41 = "What are the most frequent SIRIUS chemical structure annotations (planar structure) observed from the extracts belonging to Hibiscus syriacus?"
    q42 = "Retrieve the Spec2Vec documents  associated with MS2 spectra  from the lab extracts  of Tabernaemontana coffeoides"
    q43 = "What are the ChEMBL targets (ChEMBLTarget) linked to ChEMBL assay results (ChEMBLAssayResults) for chemicals (ChEMBLChemical) sharing InChIKeys (InChIkey) with SIRIUS structural annotations (SiriusStructureAnnotation)?"
    q44 = "Retrieve the most frequent Spec2Vec peaks and losses characterizing the MS2 spectra from the lab extracts of Tabernaemontana coffeoides."
    q45 = "Which lab extracts have bioassay results with inhibition percentages above 50% against Leishmania donovani target at 10 µg/mL?"
    q46 = "List the LC-MS features that have a chemical class annotation by CANOPUS and have a retention time between 5-7 minutes."
    q47 = "Retrieve the lab extracts that have more than 2,000 features detected. "
    q49 = "What are the LCMS features  that have feature areas  greater than 1,000,000 in positive ionization mode ?"
    q50 = "List the lab extracts  that have bioassay results  at  2µg/mL against Trypanosoma brucei rhodesiense ."
    q51 = "Which ChEMBL documents cited in ChEMBL assay results involve compounds (identified by InChIKeys) that are also observed in SIRIUS structural annotations within lab extracts, and which lab extracts contain the highest number of these shared compounds?"
    q54 = "For the LC-MS feature observed in the extracts of Tabernaemontana coffeoides, retrieve those that are annotated with a NPCPathways with CANOPUS."
    q55 = "Retrieve the Wikidata IDs  of chemical entities  classified as Terpenoids in the lab extracts of Tabernaemontana coffeoides."
    q57 = "Retrieve the Wikidata IDs of chemical entities from Desmodium heterophyllum that are annotated as rotenoids by CANOPUS and have ChEMBL assay results showing activity against Trypanosoma cruzi. Provide also the USIs to the corresponding MS/MS spectra."
    q58 = "Retrieve the retention times and parent masses of LCMS features annotated as Terpenoids by CANOPUS in Tabernaemontana coffeoides."
    q63 = "What are the most frequent adducts of LCMS features annotated by SIRIUS detected in positive ionization mode from Tabernaemontana coffeoides?"
    q64 = "What are the LCMS features with the highest area annotated as alkaloids by CANOPUS in Tabernaemontana coffeoides extracts?"
    q65 = "List the tissue types used to produce the lab extracts of Tabernaemontana coffeoides. Provide the tissue types  and lab extracts. "
    q66 = "Which LCMS features from Tabernaemontana coffeoides have MS2 spectrum that have Spec2Vec peaks with values above 0.8? Provide MS2 spectra."
    q67 = "What are the cosmic scores  and zodiac scores  associated with SIRIUS structural annotations  for LCMS features  from Tabernaemontana coffeoides?"
    q69 = "Retrieve the mass differences and cosine similarity scores for spectral pairs involving MS2 spectra from Desmodium heterophyllum."
    q71 = "What are the LC-MS features that have GNPS library analogs annotation in Tabernaemontana coffeoides? Provide the features."
    q72 = "Which ISDB annotations  have consistency scores  above 0.7 and taxonomic scores above 0.5 for LCMS features from Tabernaemontana coffeoides? Provide annotations."
    q73 = "Retrieve the top-10 lab extracts with the most unique features detected (minimum feature area intensity of 500,000)."
    q74 = "What are the retention times and adduct types of LCMS features from Desmodium heterophyllum annotated by SIRIUS with a cosmic score greater than 0.4??"
    q75 = "Retrieve the top 5 tissues used to produce lab extracts that contain compounds with inhibition activity greater than 70% against Leishmania donovani target at 10 µg/mL."
    q76 = "List the top 3 lab extracts with the highest number of unique compounds annotated by CANOPUS with a probability greater than 0.9."
    q2_bis = "Which extracts have features (pos ionization mode) annotated as the class, isoquinoline-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count? Group by extract. "
    q3_bis = "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode."
    q5_bis = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Leishmania donovani target?"
    q77 = "Which chemical compounds from Tabernaemontana coffeoides extract have the same CANOPUS and ISDB  annotations in positive and negative ionization mode? Provide the Inchikey2Ds of the compounds. "
    q78 = "Which chemical compounds demonstrated inhibition rates above 50% against Trypanosoma cruzi target? Provide the Inchikey2Ds of compounds. "
    q79 = "Provide the InchiKey2Ds of chemical compounds that have reported ChEMBL activity with activity type IC50 and activity values below 500 nM against Leishmania donovani target."
    q80 = "Which chemical compounds have been observed both in ChEMBL documents and in SIRIUS structural annotations within lab extracts. Provide the Inchikey2Ds of compounds."
    q81 = "Which chemical entities are classified as Terpenoids in the lab extracts of Tabernaemontana coffeoides? Provide the Inchikeys 10 compounds."
    q82 = "Which chemical entities are annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability above 0.5? Provide the Inchikeys and corresponding Wikidata IDs of 10 chemical compounds."
    q83 = "Retrieve the Inchikeys of chemical entities from Desmodium heterophyllum that are annotated as rotenoids by CANOPUS and have ChEMBL assay results showing activity against Trypanosoma cruzi. Provide 10 Inchikeys."
    q84 = "Retrieve the Inchikeys and corresponding Wikidata IDs of chemical compounds with inhibition activity greater than 70% against Leishmania donovani target at 10 µg/mL. Restrict to 10 Inchikeys. "
    q85 = "Which chemical entities from Melochia umbellata taxon in pos ionization mode have features annotated by SIRIUS? Provide 10 Inchikeys and corresponding Wikidata IDs."
    q86 = "What are the InChIKey2Ds and corresponding Wikidata IDs of chemical entities associated with LCMS features in positive ionization mode that have an ISDB annotation and a feature area greater than 1,000,000? "
    q87 = "Which chemical compounds detected in extracts of Desmodium heterophyllum are annotated as alkaloids in positive and negative ionization modes by SIRIUS? Provide the InChIKeys of 10 compounds."
    q93 = "What are the chemical compounds with mass greater than 800 Da detected in LCMS features of Craterispermum laurinum? Provide the InChIKeys and molecular masses of the top 10 compounds."
    q94 = "List the chemical compounds from Tabernaemontana coffeoides that have both ISDB and SIRIUS structural annotations matching a retention time of less than 5 minutes. Provide the InChIKey2Ds of compounds."
    q97 = "Which chemical compounds are detected in positive ionization mode from Tabernaemontana coffeoides plant extract? Provide the InChIKey2Ds of compounds."
    q99 = "What are the chemical compounds annotated by ISDB in extracts of Desmodium heterophyllum? Provide the InChIKeys  and corresponding Wikidata IDs of 10 compounds."
    q99_bis = "What are the InChIKey2Ds of chemical entities annotated by ISDB in the lab extracts of Desmodium heterophyllum?"
    q41_bis = "What are the most frequent SIRIUS chemical structure annotations (planar structure) observed from the extracts belonging to Hibiscus syriacus? Provide the InChiKey2Ds of annotations."
    #process_workflow(workflow, q1)


    process_workflow(workflow, question)


if __name__ == "__main__":
    main()
