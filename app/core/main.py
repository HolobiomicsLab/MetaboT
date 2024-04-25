import configparser
import pickle
from pathlib import Path

from langchain_community.chat_models import ChatOpenAI
import os

from langsmith import Client
from app.core.graph_management.RdfGraphCustom import RdfGraph
from app.core.agents.agents_factory import create_all_agents
from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from app.core.utils import setup_logger


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


def llm_creation():
    """
    Reads the parameters from the configuration file params.ini and initializes the language models.
    """
    config = configparser.ConfigParser()
    config.read(params_path)

    sections = ["llm", "llm_preview"]
    models = {}

    for section in sections:
        temperature = config[section]["temperature"]
        model_id = config[section]["id"]
        max_retries = config[section]["max_retries"]
        llm = ChatOpenAI(
            temperature=temperature,
            model=model_id,
            max_retries=max_retries,
            verbose=True,
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
        f"KGBot Testing - Interpreter_agent"  # Please update the name here if you want to create a new project for separating the traces.
    )
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    client = Client()

    # #Check if the client was initialized
    print(f"Langchain client was initialized: {client}")


def main():
    langsmith_setup()
    endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
    graph = link_kg_database(endpoint_url)
    models = llm_creation()
    agents = create_all_agents(models, graph)
    workflow = create_workflow(agents)

    q1 = "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey of the annotations?"
    q2 = "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count of features as aspidosperma-type alkaloids? Group by extract."
    q3 = "Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"
    q4 = "Among the SIRIUS structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon, which ones are reported in the Tabernaemontana genus in Wikidata? Can use service <https://query.wikidata.org/sparql> to run a subquery to wikidata within the sparql query"
    q5 = "Which compounds have annotations with chembl assay results indicating reported activity against T. cruzi by looking at the cosmic, zodiac and taxo scores?"
    q6 = "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- adduct (+/- 5ppm)."
    q7 = "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D"
    q8 = "Which features were annotated as 'Tetraketide meroterpenoids' by SIRIUS, and how many such features were found for each species and plant part?"
    q9 = "What are all distinct submitted taxons for the extracts in the knowledge graph?"
    q10 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q11 = "Count all the species per family in the collection"
    q12 = "Taxons can be found in enpkg:LabExtract. Find the best URI of the Taxon in the context of this question : \n Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"

    process_workflow(workflow, q6)


if __name__ == "__main__":

    main()
