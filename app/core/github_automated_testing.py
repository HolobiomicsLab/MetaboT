#Automated testing file for Github

# Importing the Libraries

import re
import os
import functools
import sys
import argparse
from datetime import datetime
from typing import List, Tuple, Union
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, create_openai_tools_agent, AgentType, initialize_agent, load_tools
from langchain.prompts import BaseChatPromptTemplate
from langchain.utilities import SerpAPIWrapper
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from langchain import hub
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.evaluation import EvaluatorType
from langsmith import Client
from langsmith.evaluation import EvaluationResult, run_evaluator
from langsmith.schemas import Example, Run
from langchain.smith import arun_on_dataset, run_on_dataset, RunEvalConfig
from RdfGraphCustom import RdfGraph
from smile_resolver import smiles_to_inchikey
from chemical_resolver import ChemicalResolver
from target_resolver import target_name_to_target_id
from taxon_resolver import TaxonResolver
from sparql import GraphSparqlQAChain

# Defining and importing LangSmith
# For now, all runs will be stored in the "KGBot Testing - GPT4"
# If you want to separate the traces to have a better control of specific traces.
# Metadata as llm version and temperature can be obtaneid from traces. 

def main(args):
    # The main function for setting and running the automated testing 

    now = datetime.now()
    formatted_now = now.strftime("%m-%d-%Y %H:%M:%S")

    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "KGBot Github Automated Testing - GPT4" #Please update the name here if you want to create a new project for separating the traces. 
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    except Exception as e:
        print(f"An unexpected error occured: {e}")

    try:
        client = Client()
    except Exception as e:
        print(f"An unexpected error occured while initializing the environment for LangSmith")


    # Endpoint pointing to the Knowledge Graph
    endpoint_url = 'https://enpkg.commons-lab.org/graphdb/repositories/ENPKG'
    graph = RdfGraph(query_endpoint=endpoint_url, standard="rdf")
        
    #Defining some parameters for the LLM
    temperature = args.temperature
    print(temperature)
    llm_model = args.llm_model

    # https://api.python.langchain.com/en/latest/chat_models/langchain_community.chat_models.openai.ChatOpenAI.html?highlight=chatopenai#
    # This one is set for SparqlQuery
    llm_gpt4 = ChatOpenAI(temperature=temperature, 
                        model= "gpt-4", # For using in Sparql
                        max_retries=3,
                        verbose=True,
                        model_kwargs={"top_p": 0.95})
        
    llm = ChatOpenAI(temperature=temperature, 
                            model=llm_model,  # This is the one set by the user. The default is "GPT-4-turbo"
                            max_retries=3,
                            verbose=True,
                            model_kwargs={"top_p": 0.95})

    # The GraphSparqlQAChain.from_llm was changed to accept two versions of GPT.
    sparql_chain = GraphSparqlQAChain.from_llm(llm=llm, llm_sparql=llm_gpt4, graph=graph, verbose=True)
    chem_res = ChemicalResolver.from_llm(llm=llm, verbose=True)
    taxon_res = TaxonResolver()

    class ChemicalInput(BaseModel):
        query: str = Field(description="natural product compound string")

    class SparqlInput(BaseModel):
        question: str = Field(description="the original question from the user")
        entities: str = Field(description="strings containing for all entities, entity name and the corresponding entity identifier")

    # Defining the tools that can be accessed
    tools = [
        StructuredTool.from_function(
            name = "CHEMICAL_RESOLVER",
            func = chem_res.run,
            description="The function takes a natural product compound string as input and returns a InChIKey, if InChIKey not found, it returns the NPCClass, NPCPathway or NPCSuperClass.",
            args_schema=ChemicalInput,
        ),
        StructuredTool.from_function(
            name = "TAXON_RESOLVER",
            func=taxon_res.query_wikidata,
            description="The function takes a taxon string as input and returns the wikidata ID.",
        ),
        StructuredTool.from_function(
            name = "TARGET_RESOLVER",
            func=target_name_to_target_id,
            description="The function takes a target string as input and returns the ChEMBLTarget IRI.",
        ),
        StructuredTool.from_function(
            name = "SMILE_CONVERTER",
            func=smiles_to_inchikey,
            description="The function takes a SMILES string as input and returns the InChIKey notation of the molecule.",
        ),
        StructuredTool.from_function(
            name = "SPARQL_QUERY_RUNNER",
            func=sparql_chain.run,
            description="The agent resolve the user's question by querying the knowledge graph database. Input should be a question and the resolved entities in the question.",
            args_schema=SparqlInput,
            # return_direct=True,
        ),
    ]

    tool_names = [tool.name for tool in tools]

    # Defining the Prompt for the search

    system_message = """You are an entity resolution agent for the SPARQL_QUERY_RUNNER.
    You have access to the following tools:
    {tool_names}

    If the question ask anything about any entities that could be natural product compound, find the relevant IRI to this chemical class using CHEMICAL_RESOLVER. Input is the chemical class name.

    If a taxon is mentionned, find what is its wikidata IRI with TAXON_RESOLVER. Input is the taxon name.

    If a target is mentionned, find the ChEMBLTarget IRI of the target with TARGET_RESOLVER. Input is the target name.

    If a SMILE structure is mentionned, find what is the InChIKey notation of the molecule with SMILE_CONVERTER. Input is the SMILE structure.
            
    Give me units relevant to numerical values in this question. Return nothing if units for value is not provided.
    Be sure to say that these are the units of the quantities found in the knowledge graph.
    Here is the list of units to find:
        "retention time": "minutes",
        "activity value": null, 
        "feature area": "absolute count or intensity", 
        "relative feature area": "normalized area in percentage", 
        "parent mass": "ppm (parts-per-million) for m/z",
        "mass difference": "delta m/z", 
        "cosine": "score from 0 to 1. 1 = identical spectra. 0 = completely different spectra"

    Use SPARQL_QUERY_RUNNER tool to answer the question. Input contains the user question + the list of tuples of strings of the resolved entities and units found in previous steps.

    If no results tell the user how to improve their question and give the SPARQL query that have been returned by the SPARQL_QUERY_RUNNER.

    Give the answer to the user.
            
    """.format(tool_names="\n".join(tool_names))

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    # Creating the Agent and the executor
    agent = create_openai_tools_agent(tools=tools, llm=llm, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


    # Since chains can be stateful (e.g. they can have memory), we provide
    # a way to initialize a new chain for each row in the dataset. This is done
    # by passing in a factory function that returns a new chain for each row.
    def create_agent(prompt, llm, tools):
        runnable_agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm
            | OpenAIFunctionsAgentOutputParser()
        )
        return AgentExecutor(agent=runnable_agent, tools=tools, verbose=True, handle_parsing_errors=True)


    # Defining a custom evaluator that checks if the generated answer is uninformative
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


    # Defining initial evaluators parameters
    evaluators = [
        EvaluatorType.QA,
        EvaluatorType.EMBEDDING_DISTANCE,
        ]

    # Appending some standard LangSmith Labeled Criteria depeding on the passed arguments
    if args.conciseness: evaluators.append(RunEvalConfig.LabeledCriteria("conciseness"))
    if args.relevance: evaluators.append(RunEvalConfig.LabeledCriteria("relevance"))
    if args.coherence: evaluators.append(RunEvalConfig.LabeledCriteria("coherence"))
    if args.harmfulness: evaluators.append(RunEvalConfig.LabeledCriteria("harmfulness"))
    if args.maliciousness: evaluators.append(RunEvalConfig.LabeledCriteria("maliciousness"))
    if args.helpfulness: evaluators.append(RunEvalConfig.LabeledCriteria("helpfulness"))
    if args.controversiality: evaluators.append(RunEvalConfig.LabeledCriteria("controversiality"))
    if args.misogyny: evaluators.append(RunEvalConfig.LabeledCriteria("misogyny"))
    if args.criminality: evaluators.append(RunEvalConfig.LabeledCriteria("criminality"))
    if args.insensitivity: evaluators.append(RunEvalConfig.LabeledCriteria("insensitivity"))

    # Add the LabeledScoreString evaluator unconditionally for how accurate is the answer based on the Reference Output
    evaluators.append(RunEvalConfig.LabeledScoreString({"accuracy": 
        """Score 1: The answer is completely unrelated to the reference.
        Score 3: The answer has minor relevance but does not align with the reference.
        Score 5: The answer has moderate relevance but contains inaccuracies.
        Score 7: The answer aligns with the reference but has minor errors or omissions.
        Score 10: The answer is completely accurate and aligns perfectly with the reference."""},
        normalize_by=10))
    
    # Configuring the full evaluator
    evaluation_config = RunEvalConfig(
        evaluators=evaluators,
        custom_evaluators=[check_not_idk],
        )

    # Running the evaluation on the dataset
    chain_results = run_on_dataset(
        dataset_name=args.dataset,
        llm_or_chain_factory=functools.partial(create_agent, prompt=prompt, llm=llm, tools=tools),
        evaluation=evaluation_config,
        verbose=True,
        client=client,
        project_name=f"KGBot_Automated_Agent_testing-{formatted_now}",
        # Project metadata communicates the experiment parameters,
        # Useful for reviewing the test results
        project_metadata={
            "env": "Automated",
            "model": f"gpt-4{args.llm_model}",
            "prompt": "",
        },
    )

    print(chain_results)

def run_main():
    
    # For running with a command line
    parser = argparse.ArgumentParser(
        description = "A runnable command line for automated testing of LangSmith"
    )

    # Some standard parameters for running the tests
    parser.add_argument("--llm_model", type=str, default="gpt-4-0125-preview", help="The model of usage for ChatGPT")
    parser.add_argument("--temperature", type=int, default=0.3, help="The temperature for the LLM")
    parser.add_argument("--dataset", type=str, default="KGBot_sanity_eval", help="The dataset for running the tests. Default is KGBot_sanity_eval")

    # Langsmith
    evaluators = parser.add_argument_group("Evaluators", "LangSmith standard evaluators")
    evaluators.add_argument("--conciseness", type=bool, default=False, help="LangSmith Evaluator conciseness")
    evaluators.add_argument("--relevance", type=bool, default=False, help="LangSmith Evaluator relevance")
    evaluators.add_argument("--coherence", type=bool, default=False, help="LangSmith Evaluator coherence")
    evaluators.add_argument("--harmfulness", type=bool, default=False, help="LangSmith Evaluator harmfulness")
    evaluators.add_argument("--maliciousness", type=bool, default=False, help="LangSmith Evaluator maliciousness")
    evaluators.add_argument("--helpfulness", type=bool, default=True, help="LangSmith Evaluator helpfulness")
    evaluators.add_argument("--controversiality", type=bool, default=False, help="LangSmith Evaluator controversiality")
    evaluators.add_argument("--misogyny", type=bool, default=False, help="LangSmith Evaluator misogyny")
    evaluators.add_argument("--criminality", type=bool, default=False, help="LangSmith Evaluator criminality")
    evaluators.add_argument("--insensitivity", type=bool, default=False, help="LangSmith Evaluator insensitivity")

    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    run_main()