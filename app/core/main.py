from prompts import (
    SPARQL_GENERATION_SELECT_PROMPT,
    SPARQL_QA_PROMPT,
)
from app.core.RdfGraphCustom import RdfGraph
from langchain.chat_models import ChatOpenAI
from sparql import GraphSparqlQAChain
from chemical_resolver import ChemicalResolver
import pickle


if __name__ == "__main__":

    
    endpoint_url = 'https://enpkg.commons-lab.org/graphdb/repositories/ENPKG'
    # endpoint_url = 'https://query.wikidata.org/sparql'

    graph = RdfGraph(
        query_endpoint=endpoint_url,
        standard="rdf")
    
    # print(graph.get_schema)
    
    # with open('drafts/app/graphs/graph_namespaceNone.pkl', 'wb') as output_file:
    #     pickle.dump(graph, output_file)
        
        
    # with open('drafts/app/graphs/graph.pkl', 'rb') as input_file:
    #     graph = pickle.load(input_file)

    print(graph.get_schema)
    
    temperature = 0.3
    model_id = "gpt-4" 
    
    # https://api.python.langchain.com/en/latest/chat_models/langchain_community.chat_models.openai.ChatOpenAI.html?highlight=chatopenai#
    model = ChatOpenAI(temperature=temperature, 
                       model=model_id, # default is 'gpt-3.5-turbo'
                        max_retries=3,
                        verbose=True,
                        model_kwargs={
                            "top_p": 0.95,
                            }
                        )
    
    #https://api.python.langchain.com/en/latest/_modules/langchain/chains/graph_qa/sparql.html#
    chain = GraphSparqlQAChain.from_llm(
        model, graph=graph, verbose=True
    )
 
    
    q1 = 'How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey of the annotations?'
    q2 = 'Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decresing count of features as aspidosperma-type alkaloids? Group by extract.'
    q3 = 'Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?'
    q4 = 'Among the SIRIUS structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon, which ones are reported in the Tabernaemontana genus in Wikidata? Can use service <https://query.wikidata.org/sparql> to run a subquery to wikidata within the sparql query'
    q5 = 'Which compounds have annotations with chembl assay results indicating reported activity against T. cruzi by looking at the cosmic, zodiac and taxo scores?'
    q6 = 'Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- adduct (+/- 5ppm).'
    q7 = 'For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D'
    q8 = "Which features were annotated as 'Tetraketide meroterpenoids' by SIRIUS, and how many such features were found for each species and plant part?"
    q9 = "What are all distinct submitted taxons for the extracts in the knowledge graph?"
    q10 = "What are the taxons, lab process and label (if one exists) for each sample? Sort by sample and then lab process"
    q11 = "Count all the species per family in the collection"
    
    q12 = "Taxons can be found in enpkg:LabExtract. Find the best URI of the Taxon in the context of this question : \n Among the structural annotations from the Tabernaemontana coffeoides (Apocynaceae) seeds extract taxon , which ones contain an aspidospermidine substructure, CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45?"
    
    chain.run(q3)