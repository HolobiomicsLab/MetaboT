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
from app.core.memory.custom_sqlite_file import SqliteSaver
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

    sections = ["llm", "llm_preview", "llm_o", "llm_3_5", "llm_mini"]
    models = {}

    # Get the OpenAI API key from the configuration file or the environment variables if none as passed. This allows Streamlit to pass the API key as an argument.
    openai_api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")

    for section in sections:
        temperature = config[section]["temperature"]
        model_id = config[section]["id"]
        max_retries = config[section]["max_retries"]
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
    # #Setting up the LangSmith
    # #For now, all runs will be stored in the "KGBot Testing - GPT4"
    # #If you want to separate the traces to have a better control of specific traces.
    # #Metadata as llm version and temperature can be obtained from traces.

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = (
        f"KGBot Testing - IMPROVEMENT chain"  # Please update the name here if you want to create a new project for separating the traces.
    )
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    client = Client()

    # #Check if the client was initialized
    print(f"Langchain client was initialized: {client}")


def main():
    # parser = argparse.ArgumentParser(description="Process a workflow with a predefined or custom question.")
    # parser.add_argument('-q', '--question', type=int, choices=range(1, 13),
    #                     help="Choose a standard question number from 1 to 12.")
    # parser.add_argument('-c', '--custom', type=str,
    #                     help="Provide a custom question.")
    #
    # args = parser.parse_args()
    #
    # standard_questions = [
    #     "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey of the annotations?",
    #     "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids? Group by extract.",
    #     "Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?",
    #     "Among the SIRIUS structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon, which ones are reported in the Tabernaemontana genus in Wikidata? Can use service <https://query.wikidata.org/sparql> to run a subquery to wikidata within the sparql query",
    #     "Which compounds have annotations with chembl assay results indicating reported activity against T. cruzi by looking at the cosmic, zodiac and taxo scores?",
    #     "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- adduct (+/- 5ppm).",
    #     "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D",
    #     "Which features were annotated as 'Tetraketide meroterpenoids' by SIRIUS, and how many such features were found for each species and plant part?",
    #     "What are all distinct submitted taxons for the extracts in the knowledge graph?",
    #     "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process",
    #     "Count all the species per family in the collection",
    #     "Taxons can be found in enpkg:LabExtract. Find the best URI of the Taxon in the context of this question: Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon, which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"
    # ]
    #
    # if args.question:
    #     question = standard_questions[args.question - 1]
    # elif args.custom:
    #     question = args.custom
    # else:
    #     print("You must provide either a standard question number or a custom question.")
    #     return

    langsmith_setup()
    endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    # endpoint_url = "https://enpkg.commons-lab.org/graphdb/sparql"
    graph = link_kg_database(endpoint_url)
    models = llm_creation()
    agents = create_all_agents(models, graph)
    workflow = create_workflow(agents)

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
    q4 = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Trypanosoma cruzi?"
    q5 = "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm). Provide the features and retention time."
    q6 = "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D"
    q7 = "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?"
    q8 = "What are all distinct submitted taxons for the extracts of the Desmodium heterophyllum?"
    q9 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q10 = "What are the retention times, parent masses, and associated Spec2Vec peaks for features in the LC-MS analysis of the plant Rumex nepalensis in positive ion mode?"
    q11 = "How many distinct InChIKey2D are present among the structural annotations?"
    q11_bis = "How unique InChIKey2D are among the structural annotations?"
    q12 = "How many distinct Wikidata identifiers (WD IDs) have InChIKey (IK) values that share the same InChIKey2D among annotations?"
    q12_bis = "How many distinct Wikidata identifiers (WD IDs) have the same metabolite annotation (considering only the plannar structure)?"
    q13 = "Count the number of LCMS features in negative ionization mode"
    q14 = "Which molecules (represented by their InChIkey) have reported ChEMBL activity with activity type  IC50 and activity values below 500 nM against Leishmania donovani target?"
    q15= "What are the mass spectrometry features detected for the plant Rumex nepalensis?"
    q16 = "What are the chemical structure ISDB annotations for Lovoa trichilioides ?"
    q18 = "Provide the Wikidata IDs of chemical structures and bioassay screening results of compounds identified from Musanga cecropioides that show significant inhibition percentages against Trypanosoma brucei rhodesiense?"
    q19 = "Which compounds derived from Craterispermum laurinum are annotated as Aspidosperma-type alkaloids, and what are their bioassay screening results against Leishmania donovani? Provide the Wikidata IDs."
    q20 = "What are the Wikidata id's of annotations provided by ISDB for compounds derived from Lovoa trichilioides? (similar to q17)"
    q21 = "What are the mass spectrometry features detected in the positive ionization mode for Musanga cecropioides? (similar to q16)"
    q22 = "Can you identify the compounds isolated from Musanga cecropioides that have been annotated by CANOPUS as belonging to the Isoquinoline-type alkaloids chemical class, and provide their structures as SMILES and their bioactivity data against Leishmania donovani as sourced from ChEMBL??"
    q23 = "Can you identify the CANOPUS-classified chemical classes for the chemical entity with Wikidata ID Q105112192, which shows activity against Trypanosoma cruzi in bioassays? Additionally, provide the SMILES notation and the molecular mass of this compound."
    q23_modified = "Can you retrieve the CANOPUS-classified ns1:NPCClass for the chemical entity identified by the Wikidata ID ns1:WDChemical Q105112192, which has demonstrated activity against Trypanosoma cruzi in the ns2:ChEMBLAssayResults? Please also provide the ns1:has_smiles notation and ns1:has_parent_mass of this chemical entity."
    q24 = "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract?"
    q24_modified = "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract, and which ns1:NPCClass from CANOPUS annotations do these compounds belong to?"
    q25 = "Which ns1:NPCClass classified by CANOPUS has the highest inhibition percentage against Trypanosoma cruzi?"
    q26 = "Can you provide the SMILES notation and the Wikidata IDs for the compound with the highest precursor ion mass in the MS2 spectra from extracts of Lovoa trichilioides by looking at SIRIUS annotations?"
    q27 = "What are the retention times and feature areas of LCMS features extracted from Lovoa trichilioides?"
    q27_modified = "What are the retention times and molecular masses of compounds identified in the negative ionization mode LCMS analysis from  Lovoa trichilioides extracts, and what are the CANOPUS chemical class annotations for those features?"
    q28 = "Which lab extracts from Melochia umbellata  yield compounds that, when analyzed in positive ionization mode LCMS, have a retention time of less than 2 minutes and demonstrate an inhibition percentage greater than 70% in bioassay results? Provide lab extracts, retention times and inhibition percentage."
    q29 = "Which compounds from Desmodium heterophyllum extracts have annotations from both ISDB and SIRIUS, and what are their molecular masses?"
    q30 = "What is the distribution of chemical superclasses in the LCMS features annotated by CANOPUS identified from Desmodium heterophyllum extracts?"
    q31 = "What are the CANOPUS annotations for pairs of features from Desmodium heterophyllum extracts that share a cosine similarity score greater than 0.8? Provide the features and annotations for each feature."
    q32 = "Which extracts from Desmodium heterophyllum contain compounds annotated with molecular masses greater than 800 Da and demonstrate inhibition rates above 50% against Trypanosoma cruzi? Provide the lab extracts."
    q32_bis = "Which plant has extracts containing compounds that demonstrated inhibition rates above 50% against Trypanosoma cruzi and are above 800 Da in mass? Provide the lab extracts"
    q33 = "Which samples  contain the largest amount of chemical compounds annotated as diterpene esters by CANOPUS?"
    q34 = "What are the SIRIUS structural annotations (SiriusStructureAnnotation) associated with the MS2 spectra (MS2Spectrum) from the lab extracts (LabExtract) of Tabernaemontana coffeoides ?"
    q35 = "Retrieve the InChIKeys (InChIkey) of chemical entities (ChemicalEntity) annotated by ISDB (IsdbAnnotation) in the lab extracts (LabExtract) from Tabernaemontana coffeoides."
    q36 = "What NPCClasses (NPCClass) are linked to MS2 spectra (MS2Spectrum) annotated by CANOPUS (SiriusCanopusAnnotation) from Tabernaemontana coffeoides?"
    q37 = "List the bioassay results (BioAssayResults) at 10µg/mL against T.cruzi (Tcruzi10ugml) for lab extracts (LabExtract) of Tabernaemontana coffeoides."
    q38 = "Retrieve the ChEMBL assay results (ChEMBLAssayResults) for ChEMBL chemicals (ChEMBLChemical) that share InChIKeys (InChIkey) with SIRIUS structural annotations (SiriusStructureAnnotation) from the lab extracts (LabExtract) of Tabernaemontana coffeoides."
    q39 = "Which bioassay results (BioAssayResults) at 10µg/mL against T.cruzi (Tcruzi10ugml) are linked to LCMS features (LCMSFeature) detected in negative ionization mode (LCMSAnalysisNeg) from Tabernaemontana coffeoides?"
    q40 = "What are the MS2 spectra (MS2Spectrum) associated with LCMS features (LCMSFeature) detected in negative ionization mode (LCMSAnalysisNeg) from the lab extracts (LabExtract) of Tabernaemontana coffeoides? Provide usi of spectra."
    q41 = "What are the most frequent SIRIUS chemical structure annotations (planar structure) observed from the extracts belonging to Hibiscus syriacus?"
    q42 = "Retrieve the Spec2Vec documents  associated with MS2 spectra  from the lab extracts  of Tabernaemontana coffeoides"
    q43 = "What are the ChEMBL targets (ChEMBLTarget) linked to ChEMBL assay results (ChEMBLAssayResults) for chemicals (ChEMBLChemical) sharing InChIKeys (InChIkey) with SIRIUS structural annotations (SiriusStructureAnnotation)?"
    q44 = "Retrieve the most frequent Spec2Vec peaks and losses characterizing the MS2 spectra from the lab extracts of Tabernaemontana coffeoides."
    q44_bis = "Retrieve the most frequent Spec2Vec peaks and losses characterizing the MS2 spectra from the lab extracts of Tabernaemontana coffeoides."
    q45 = "Which lab extracts have bioassay results with inhibition percentages above 50% against Leishmania donovani  at 10 µg/mL?"
    q46 = "List the LC-MS features that have a chemical class annotation by CANOPUS and have a retention time between 5-7 minutes."
    q47 = "Retrieve the lab extracts that have more than 2,000 features detected. "
    q48 = "Which MS2 spectra  have Spec2Vec documents containing Spec2Vec peaks with values above 1000?"
    q49 = "What are the LCMS features  that have feature areas  greater than 1,000,000 in positive ionization mode ?"
    q50 = "List the lab extracts  that have bioassay results  at  2µg/mL against Trypanosoma brucei rhodesiense ."
    q51 = "Which ChEMBL documents cited in ChEMBL assay results involve compounds (identified by InChIKeys) that are also observed in SIRIUS structural annotations within lab extracts, and which lab extracts contain the highest number of these shared compounds?"
    q52 = "Which LCMS features have the same SIRIUS structural annotation for the adducts [M+H]+ and [M+Na]+ for Tabernaemontana coffeoides extracts?"
    q53 = "List the InChIKey2Ds  that are associated with both SIRIUS structural annotations and ISDB annotations."
    q54 = "For the LC-MS feature observed in the extracts of Tabernaemontana coffeoides, retrieve those that are annotated with a NPCPathways with CANOPUS."
    q55 = "Retrieve the Wikidata IDs  of chemical entities  classified as Terpenoids in the lab extracts of Tabernaemontana coffeoides."
    q56 = "List the MS2 spectra from Tabernaemontana coffeoides that have ISDB annotations  matching the SMILES CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45."
    q57 = "Retrieve the Wikidata IDs of chemical entities from Desmodium heterophyllum that are annotated as rotenoids by CANOPUS and have ChEMBL assay results showing activity against Trypanosoma cruzi. Provide also the USIs to the corresponding MS/MS spectra"
    q58 = "Retrieve the retention times and parent masses of LCMS features annotated as Terpenoids by CANOPUS in Tabernaemontana coffeoides."
    q59 = "What are the SIRIUS structural annotations  linked to LCMS features that match the SMILES CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"
    q60 = "List the Spec2Vec similarities between MS2 spectra of the compounds that were annotated as  alkaloids and Terpenoids by CANOPUS from Desmodium heterophyllum."
    q61 = "Which chemical entities  from Tabernaemontana coffeoides have both ISDB annotations and SIRIUS annotations annotated as alkaloids? Provide the Inchikeys."
    q62 = "Which LCMS features from Tabernaemontana coffeoides annotated by SIRIUS have raw spectra and associated USIs ?"
    q63 = "What are the most frequent adducts of LCMS features annotated by SIRIUS detected in positive ionization mode from Tabernaemontana coffeoides?"
    q64 = "What are the LCMS features with the highest area annotated as alkaloids by CANOPUS in Tabernaemontana coffeoides extracts?"
    q65 = "List the tissue types used to produce the lab extracts of Tabernaemontana coffeoides. Provide the tissue types  and lab extracts. "
    q66 = "Which LCMS features from Tabernaemontana coffeoides have MS2 spectrum that have Spec2Vec peaks with values above 0.8? Provide MS2 spectra."
    q67 = "What are the cosmic scores  and zodiac scores  associated with SIRIUS structural annotations  for LCMS features  from Tabernaemontana coffeoides?"
    q68 = "Which LCMS features have GNPS dashboard views and GNPS LCMS links, and are associated with lab extracts of Tabernaemontana coffeoides?"
    q69 = "Retrieve the mass differences and cosine similarity scores for spectral pairs involving MS2 spectra from Desmodium heterophyllum."
    q70 = "Retrieve the adducts, SIRIUS scores, and spectral scores from SIRIUS structural annotations  associated with LCMS features of Tabernaemontana coffeoides."
    q71 = "What are the LC-MS features that have GNPS library analogs annotation in Tabernaemontana coffeoides? Provide the features."
    q72 = "Which ISDB annotations  have consistency scores  above 0.7 and taxonomic scores above 0.5 for LCMS features from Tabernaemontana coffeoides? Provide annotations."
    q73 = "Retrieve the top-10 lab extracts with the most unique features detected (minimum feature area intensity of 500,000)."
    q74 = "What are the retention times and adduct types of LCMS features from Desmodium heterophyllum annotated by SIRIUS with a cosmic score greater than 0.4??"
    q75 = "Retrieve the top 5 tissues used to produce lab extracts that contain compounds with inhibition activity greater than 70% against Leishmania donovani target at 10 µg/mL."

    q2_bis = "Which extracts have features (pos ionization mode) annotated as the class, isoquinoline-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count? Group by extract. "
    q3_bis = "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode."
    q5_bis = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Leishmania donovani target?"


    process_workflow(workflow, q66)

    # process_workflow(workflow, question)

if __name__ == "__main__":
    main()
