import configparser
from pathlib import Path
import pickle
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

load_dotenv()

import os

from langsmith import Client
from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.agents.agents_factory import create_all_agents
from app.core.workflow.langraph_workflow import (
    create_workflow,
    process_workflow,
)
from app.core.utils import setup_logger
from app.core.agents.agents_factory import create_all_agents


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


def get_ovh_key():
    return os.getenv("OVHCLOUD_API_KEY")


def get_huggingface_key():
    return os.getenv("HF_TOKEN")


def get_google_key():
    return os.getenv("GOOGLE_API_KEY")


def get_deepseek_key():
    return os.getenv("DEEPSEEK_API_KEY")


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

    sections = [
        "openai",
        "openai_preview",
        "openai_o",
        "openai_o_m",
        "ollama_llama_3_2",
        "ollama_llama_3_3",
        "ollama_llama_3_2_1b",
        "deepseek_deepseek-chat",
        "ovh_Meta-Llama-3_1-70B-Instruct",
        "deepseek_deepseek-reasoner",
        "groq_Llama_3_3_70B",
        "hugface_Llama_3_3_70B",
    ]
    models = {}

    # Get the OpenAI API key from the configuration file or the environment variables if none as passed. This allows Streamlit to pass the API key as an argument.
    openai_api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")

    for section in sections:
        temperature = config[section]["temperature"]
        model_id = config[section]["id"]
        max_retries = config[section]["max_retries"]
        if section.startswith("openai"):
            llm = ChatOpenAI(
                temperature=temperature,
                model=model_id,
                max_retries=max_retries,
                verbose=True,
                openai_api_key=openai_api_key,
            )
        elif section.startswith("ollama"):
            llm = ChatOllama(
                temperature=temperature,
                model=model_id,
                max_retries=max_retries,
                verbose=True,
            )

        elif section.startswith("deepseek"):
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

        elif section.startswith("groq"):
            llm = ChatGroq(
                temperature=temperature,
                model_name="llama-3.3-70b-versatile",
                verbose=True,
            )

        elif section.startswith("hugface"):
            hfe = HuggingFaceEndpoint(
                repo_id=model_id,
                task="text-generation",
                max_new_tokens=512,
                do_sample=False,
                repetition_penalty=1.03,
            )
            llm = ChatHuggingFace(llm=hfe, verbose=True)

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

    # langsmith_setup()
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
    q5 = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Trypanosoma cruzi?"
    q6 = "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm). Provide the features and retention time."
    q7 = "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D"
    q8 = "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?"
    q9 = "What are all distinct submitted taxons for the extracts?"
    q10 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q11 = "What are the retention times, parent masses, and associated Spec2Vec peaks for features in the LC-MS analysis of the plant Rumex nepalensis in positive ion mode?"
    q12 = "How many distinct InChIKey2D are present among the structural annotations?"
    q13 = "How many distinct Wikidata identifiers (WD IDs) have InChIKey (IK) values that share the same InChIKey2D among annotations?"
    q14 = "Count the number of LCMS features in negative ionization mode"
    q15 = "Which molecules (represented by their InChIkey) have reported ChEMBL activity with activity type  IC50 and activity values below 500 nM against Leishmania donovani target?"
    q16 = "What are the mass spectrometry features detected for the plant Rumex nepalensis?"
    q17 = "What are the chemical structure ISDB annotations for Lovoa trichilioides ?"
    q18 = "Provide the Wikidata IDs of chemical structures and bioassay screening results of compounds identified from Musanga cecropioides that show significant inhibition percentages against Trypanosoma brucei rhodesiense?"
    q19 = "Which compounds derived from Craterispermum laurinum are annotated as Aspidosperma-type alkaloids, and what are their bioassay screening results against Leishmania donovani? Provide the Wikidata IDs."
    q20 = "What are the Wikidata id's of annotations provided by ISDB for compounds derived from Lovoa trichilioides?"
    q21 = "What are the mass spectrometry features detected in the positive ionization mode for Musanga cecropioides?"
    q22 = "Can you identify the compounds isolated from Musanga cecropioides that have been annotated by CANOPUS as belonging to the Isoquinoline-type alkaloids chemical class, and provide their structures as SMILES and their bioactivity data against Leishmania donovani as sourced from ChEMBL??"
    q23 = "Can you identify the CANOPUS-classified chemical classes for the chemical entity with Wikidata ID Q105112192, which shows activity against Trypanosoma cruzi in bioassays? Additionally, provide the SMILES notation and the molecular mass of this compound."
    q23_modified = "Can you retrieve the CANOPUS-classified ns1:NPCClass for the chemical entity identified by the Wikidata ID ns1:WDChemical Q105112192, which has demonstrated activity against Trypanosoma cruzi in the ns2:ChEMBLAssayResults? Please also provide the ns1:has_smiles notation and ns1:has_parent_mass of this chemical entity."
    q24 = "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract?"
    q24_modified = "What is the highest inhibition percentage recorded for compounds from Rauvolfia vomitoria extract, and which ns1:NPCClass from CANOPUS annotations do these compounds belong to?"
    q25 = "Which ns1:NPCClass classified by CANOPUS has the highest inhibition percentage against Trypanosoma cruzi?"
    q26 = "Can you provide the SMILES notation and the Wikidata IDs for the compound with the highest parent mass in the MS2 spectra from extracts of Lovoa trichilioides by looking at ISDB annotations?"
    q27 = "What are the retention times and feature areas of LCMS features extracted from Lovoa trichilioides?"
    q27_modified = "What are the retention times and molecular masses of compounds identified in the negative ionization mode LCMS analysis from  Lovoa trichilioides extracts, and what are the CANOPUS chemical class annotations for those features?"
    q28 = "Which lab extracts from Melochia umbellata  yield compounds that, when analyzed in positive ionization mode LCMS, have a retention time of less than 2 minutes and demonstrate an inhibition percentage greater than 70% in bioassay results? Provide lab extracts, retention times and inhibition percentage."
    q29 = "Which compounds from Desmodium heterophyllum extracts have annotations from both ISDB and SIRIUS, and what are their molecular masses?"
    q30 = "What is the distribution of chemical superclasses in the LCMS features annotated by CANOPUS identified from Desmodium heterophyllum extracts?"
    q31 = "What are the CANOPUS annotations for pairs of features from Desmodium heterophyllum extracts that share a cosine similarity score greater than 0.8? Provide the features, annotations and cosine score."
    q32 = "Which extracts from Desmodium heterophyllum contain compounds annotated with molecular masses greater than 800 Da and demonstrate inhibition rates above 50% against Trypanosoma cruzi? Provide the lab extracts."
    q33 = "Which samples  contain the largest amount of chemical compounds annotated as diterpene esters by CANOPUS?"

    q2_bis = "Which extracts have features (pos ionization mode) annotated as the class, isoquinoline-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count? Group by extract. "
    q3_bis = "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode."
    q5_bis = "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Leishmania donovani target?"
    q_family = "Count all the species per family in the collection"
    q_substructure = "Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon, which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"

    process_workflow(workflow, q2)

    # process_workflow(workflow, question)


if __name__ == "__main__":
    main()
