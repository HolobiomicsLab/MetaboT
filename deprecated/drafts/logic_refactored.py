# general python libs
from abc import ABC, abstractmethod
import json
import os
import re
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import tiktoken
import logging

# langchain
from langchain import LLMChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, AgentType, initialize_agent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from typing import Callable, Optional, List, Any, Dict
from tools_script import SparqlTool, DBRetriever, SimpleAgent, SimpleTool
from prompts import (
    chemical_class_template,
    taxon_agent_template,
    target_prompt_template,
    structure_agent_template,
    unit_template,
)
from langchain.agents import Tool
import json
from abc import ABC, abstractmethod
from SPARQLWrapper import SPARQLWrapper, JSON
import re

from typing import Callable, Optional, List, Any, Dict


def check_token_length(content):
    token_counts = count_tokens(str(content))
    return token_counts < 3500


def count_tokens(content):
    # Initialize Tiktoken with the desired encoding model
    encoding = tiktoken.encoding_for_model("gpt-4")

    # Count the number of tokens in the TTL file
    token_count = len(encoding.encode(content))

    # print(f"The content contains {token_count} tokens.")
    return token_count


class ToolAbstract(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        executor: Callable,
        prompt_template: Optional[str] = None,
        template_formatter: Optional[Callable] = None,
        result_formatter: Optional[Callable] = None,
    ):
        self.name = name
        self.description = description
        self.executor = executor
        self.prompt_template = prompt_template
        self.template_formatter = template_formatter
        self.result_formatter = result_formatter

    @abstractmethod
    def template_format(self, query: str) -> str:
        pass

    @abstractmethod
    def result_format(self, result: str) -> Any:
        pass

    @abstractmethod
    def run_query(self, query: str) -> Any:
        pass

    @abstractmethod
    def make_tool(self) -> Tool:
        pass


class ToolMaker(ToolAbstract):
    def __init__(
        self,
        name: str,
        description: str,
        executor: Callable,
        prompt_template: Optional[str] = None,
        template_formatter: Optional[Callable] = None,
        result_formatter: Optional[Callable] = None,
    ):
        super().__init__(
            name,
            description,
            executor,
            prompt_template,
            template_formatter,
            result_formatter,
        )

    def template_format(self, query: str):
        return (
            self.template_formatter(self.prompt_template, query)
            if self.template_formatter
            else query
        )

    def result_format(self, result: str) -> Any:
        return self.result_formatter(result) if self.result_formatter else result

    def run_query(self, query: str):
        formatted_query = self.template_format(query)
        result = self.executor(formatted_query)
        return self.result_format(result)

    def make_tool(self):
        return Tool(name=self.name, description=self.description, func=self.run_query)


def sparql_executor(
    endpoint: str, query: str, timeout: int = 600, response_format=JSON
):
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(response_format)
    sparql.setTimeout(timeout)
    sparql.setQuery(query)
    return sparql.query().convert()


def sparql_result_formatter(results):
    def default_formatter(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Default formatting for SPARQL results."""
        return [{key: result[key]["value"] for key in result} for result in results]

    bindings = results["results"].get("bindings")
    if not bindings:
        return "No results were found. Please try a different query."

    formatted_results = default_formatter(bindings)
    if check_token_length(formatted_results):
        return (
            f"Results from query are too long. " "Consider running this query manually."
        )

    return formatted_results


def taxon_template_formatter(template: str, query: str):
    """Formats the given template string with values from the query.

    Args:
        template (str): The template string containing placeholders.
        query (str): The query string with comma-separated values.

    Returns:
        str: The formatted string or an error message.
    """
    placeholders = re.findall(r"(?<!{){([^{}]+)}(?!})", template)
    query_values = query.split(",")

    if len(placeholders) != len(query_values) or "" in query_values:
        return "Please provide all the required inputs."

    return template.format(*query_values)


def taxon_result_formatter(results):
    # Define a function to format the output data from the SPARQL query
    def taxon_format(output):
        formatted_data = {
            item["extract"]["value"]: {
                key: value["value"].rsplit("/", 1)[-1]
                for key, value in item.items()
                if key != "extract"
            }
            for item in output
        }

        for entity in formatted_data.values():
            entity["Type"] = "https://enpkg.commons-lab.org/kg/LabExtract"

        return formatted_data

    # .get() method on the dictionary to avoid a potential KeyError.
    bindings = results["results"].get("bindings")
    if not bindings:
        return (
            "No taxons were found. Either the specific taxon doesn't exist in the knowledge graph or the question is asking about all taxons. "
            "Either way, tell the agent to proceed."
        )

    formatted_results = taxon_format(bindings)
    if check_token_length(formatted_results):
        return (
            f"Results from query are too long. " "Consider running this query manually."
        )

    return formatted_results


if __name__ == "__main__":
    sparql_name = "SparqlQueryRunner"
    sparql_desc = "Useful to run Sparql queries after keywords have been extracted and identifiers have been found."

    sparql_tool = ToolMaker(
        name=sparql_name,
        desc=sparql_desc,
        executor=sparql_executor,
        template=None,
        template_formatter=None,
        result_formatter=sparql_result_formatter,
    ).make_tool()

    # Set the tool name and description for the TaxonLookup tool
    taxon_tool_name = "TaxonLookup"
    taxon_tool_desc = """Use tool when need to get extract ID for a species or taxon. 
                        Input should be taxon name.
                        Returns dictionary of possible extract URIs for the taxon of interest with other information."""
    taxon_template = """
    PREFIX enpkg: <https://enpkg.commons-lab.org/kg/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX enpkgmodule: <https://enpkg.commons-lab.org/module/>
    select * where {{ 
        ?extract rdf:type enpkg:LabExtract .
        ?process enpkg:has_lab_process ?extract ; 
                enpkg:submitted_taxon '{taxon}' ;
                enpkgmodule:has_broad_organe ?broad_organe ;
                enpkgmodule:has_organe ?organe ;
                enpkgmodule:has_subsystem ?subsystem ;
                enpkgmodule:has_tissue ?tissue ;
    }} 
    """
    taxon_tool = ToolMaker(
        name=taxon_tool_name,
        desc=taxon_tool_desc,
        executor=sparql_executor,
        template=taxon_template,
        template_formatter=taxon_template_formatter,
        result_formatter=taxon_result_formatter,
    ).make_tool()

    # NPCClass

    class EmbeddingsInitializer:
        def __init__(
            self,
            data,
            openai_api_key,
            chunk_size=500,
            chunk_overlap=25,
            separators=["PREFIX", "\n\n", "\n", " "],
        ):
            self.data = data
            self.openai_api_key = openai_api_key
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators
            self.text_splitter = None
            self.split_data_result = None

        def initialize(self):
            self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
            )
            logging.info("Splitting the documents...")
            self.split_data_result = self.text_splitter.create_documents(
                [str(self.data)]
            )
            logging.info(
                f"You have {len(self.split_data_result)} document(s) in your data."
            )

            embedding_function = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            return Chroma.from_documents(self.split_data_result, embedding_function)

    def default_parse(filepath: str) -> JSON:
        with open(filepath, "r") as f:
            return json.load(f)

    def get_db(filepath: str, open_ai_key: str):
        data = default_parse(filepath)
        embeddings_initializer = EmbeddingsInitializer(data, open_ai_key)
        db = embeddings_initializer.initialize()
        return db

    db = get_db(filepath, open_ai_key)

    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0.2,
        max_tokens=1500,
        openai_api_key=openai_api_key,
    )
    retriever = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=db.as_retriever(search_kwargs={"k": 4})
    )

    NPC_name = "NPCClass"
    NPC_desc = "Useful to get NPC class from extract ID."

    ### TO DO : understand kwargs. Pour prompt.format(**kwargs) dans NPC_template_formatter, ce serait plus simple
