# general python libs
import json
import os
import re
from typing import Callable, Optional, List, Any, Dict
from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
import tiktoken
import logging
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


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### HELPER FUNCTIONS ##########################################################


def count_tokens(content):
    """Counts the number of tokens in the content based on the GPT-4 encoding."""
    encoding = tiktoken.encoding_for_model("gpt-4")
    token_count = len(encoding.encode(content))
    return token_count


def check_token_length(content):
    """Checks if the content's token count is within the limit for GPT-4's processing"""
    token_counts = count_tokens(str(content))
    return token_counts < 3500


### TOOL CLASSES ##############################################################


class SparqlTool:
    """A tool to interact with SPARQL endpoints and run queries with template support.

    Attributes:
        endpoint (str): The SPARQL endpoint URL to which queries will be sent.
        tool_name (str): A name for this tool instance.
        tool_desc (str): A description of what this tool does.
        max_tokens (int): The maximum number of tokens permissible in the result.
        timeout (int): The timeout for SPARQL queries in seconds.
        prompt_template (str, optional): A template for constructing SPARQL queries.
        result_formatter (Callable, optional): A function to format the query results.
    """

    def __init__(
        self,
        endpoint: str,
        tool_name: str,
        tool_desc: str,
        max_tokens: int = 3500,
        timeout: int = 600,
        prompt_template: Optional[str] = None,
        result_formatter: Optional[Callable] = None,
    ):
        self.endpoint = endpoint
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template
        self.result_formatter = result_formatter or self._default_formatter
        self.sparql = self._initialize_sparql_connection(endpoint, timeout)
        self.matches = self._parse_inputs() if self.prompt_template else []

    def _initialize_sparql_connection(
        self, endpoint: str, timeout: int
    ) -> SPARQLWrapper:
        """Initializes the SPARQL connection."""
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        return sparql

    def _parse_inputs(self) -> List[str]:
        """Extract placeholders from the prompt template."""
        pattern = r"(?<!{){([^{}]+)}(?!})"
        return re.findall(pattern, self.prompt_template)

    def _default_formatter(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Default formatting for SPARQL results."""
        return [{key: result[key]["value"] for key in result} for result in results]

    def run_query(self, query: str) -> Any:
        """Execute a SPARQL query, with support for templated queries if prompt is set."""
        try:
            if self.prompt_template:
                kwargs = dict(zip(self.matches, query.split(",")))
                if not all(kwargs.values()):
                    return "Please provide all the required inputs."
                query = self.prompt_template.format(**kwargs)
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            return self._handle_query_results(results)
        except SPARQLWrapperException as e:
            return f"An error occurred: {e}"

    def _handle_query_results(self, results: Dict) -> Any:
        """Handles and formats the results of a SPARQL query."""
        bindings = results.get("results", {}).get("bindings")
        if bindings:
            formatted_results = self.result_formatter(bindings)
            token_count = len(formatted_results)
            if token_count > self.max_tokens:
                return f"Results are too long ({token_count} tokens). Consider running this query manually."
            return formatted_results
        return "No results found."

    def make_tool(self) -> Any:
        """Construct a tool based on the provided name, description and function."""
        return Tool(
            name=self.tool_name, description=self.tool_desc, func=self.run_query
        )


class DBRetriever:
    """
    A class used to retrieve data from a database using language models.

    Attributes:
        prompt (str): A string template to be formatted with queries for the language model.
        filepath (str): The path to the file containing the data.
        tool_name (str): The name of the tool that will be created using this retriever.
        tool_desc (str): A description of the tool.
        parser (Callable, optional): A function to parse the file data. Defaults to `default_parse` method if None is provided.
        chunk_size (int, optional): The size of text chunks that the data should be split into. Defaults to 500.
        chunk_overlap (int, optional): The number of characters that consecutive chunks overlap. Defaults to 25.
        separators (list of str): A list of string separators used in the splitting of document text.

    """

    def __init__(
        self,
        prompt: str,
        filepath: str,
        tool_name: str,
        tool_desc: str,
        parser: Callable = None,
        chunk_size: int = 500,
        chunk_overlap: int = 25,
    ):
        self.prompt = prompt
        self.filepath = filepath
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.parser = parser or self.default_parse
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["PREFIX", "\n\n", "\n", " "]

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API Key not found in environment variables.")

        self.data = None
        self.text_splitter = None
        self.data_chunks = None
        self.db = None
        self.retriever = None

        self.initialize_llm()

    @staticmethod
    def default_parse(filepath: str) -> Any:
        """Parse a JSON file and returns its contents."""
        with open(filepath, "r") as file:
            return json.load(file)

    def initialize_llm(self):
        """
        Initializes the language model with the GPT-4 model.
        """
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.2,
            max_tokens=1500,
            openai_api_key=self.openai_api_key,
        )

    def split_data(self):
        """Splits the data into chunks using a RecursiveCharacterTextSplitter."""
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
        logging.info("Splitting documents...")
        self.data_chunks = text_splitter.create_documents([str(self.data)])
        logging.info(f"{len(self.data_chunks)} document(s) in data.")

    def prepare_data(self):
        """Parses the data file, splits the data into manageable chunks, and creates embeddings."""
        try:
            self.data = self.parser(self.filepath)
            self.split_data()
            self.create_embeddings()
        except Exception as e:
            logging.error("Error during data split and embedding: %s", e, exc_info=True)

    def create_embeddings(self):
        """
        Creates embeddings for the data chunks using the OpenAIEmbeddings function.
        """
        self.embeddings_func = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.db = Chroma.from_documents(self.data_chunks, self.embeddings_func)

    def load_embeddings(self, embeddings):
        """Loads pre-existing ChromaDB embeddings into the DBRetriever."""
        self.db = embeddings

    def set_retriever(self, docs: int = 4):
        """Sets up the retriever with a specific number of documents to retrieve for each query."""
        self.retriever = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(search_kwargs={"k": docs}),
        )

    def run_query(self, query: str):
        """Runs a given query through the retriever and returns the result."""
        return self.retriever.run(self.prompt.format(question=query))

    def make_tool(self):
        """Creates and returns a Tool object if the retriever has been initialized."""
        if not self.retriever:
            raise ValueError(
                "Retriever is not initialized. Please intialize retriever using set_retriever method."
            )

        return Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=self.run_query,
        )


### SIMPLE AGENT Class #######################


class SimpleAgent:
    """
    A class representing a simple agent that can parse and respond to queries using language models.

    Attributes:
        prompt (str): The string template that will be used to format queries for the language model.
        tool_name (str): The name of the tool that encapsulates the agent's functionality.
        tool_desc (str): A description of what the tool does.
        tools (list): A list of tools or functionalities that the agent can utilize.
        parser_type (str, default 'simple'): The type of parser the agent uses to process input strings.
        model (str, default 'gpt-4'): The language model to be used by the agent.
        llm (ChatOpenAI, optional): An instance of the language model after initialization.
        id_agent (optional): An identifier for the agent once initialized, if applicable.
        llm_chain (LLMChain, optional): A language model chain that can be used if no specific tools are provided.
    """

    def __init__(
        self,
        prompt: str,
        tool_name: str,
        tool_desc: str,
        tools: list,
        parser: str = "simple",
        model: str = "gpt-4",
    ):
        self.prompt = prompt
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.tools = tools
        self.parser_type = parser
        self.model = model
        self.llm = None
        self.id_agent = None
        self.llm_chain = None

    def _initialize_agent(self):
        if not self.llm:
            self.llm = ChatOpenAI(temperature=0.8, model=self.model, verbose=True)
            if self.tools:
                self.id_agent = initialize_agent(
                    self.tools, self.llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True
                )
            else:
                self.llm_chain = LLMChain(
                    llm=self.llm,
                    prompt=PromptTemplate(
                        input_variables=["input"], template=self.prompt
                    ),
                )

    def _split_input(self, string: str):
        split = string.split(":", 1)
        return split[0], split[1] if len(split) > 1 else ""

    def run_query(self, query: str):
        keyword, question = self._split_input(query)
        prompt = PromptTemplate(
            input_variables=["input", "question"]
            if self.parser_type == "keyword_question"
            else ["input"],
            template=self.prompt,
        )

        self._initialize_agent()

        if self.parser_type == "keyword_question":
            formatted_prompt = prompt.format(input=keyword, question=question)
        else:
            formatted_prompt = prompt.format(input=query)

        agent_runner = self.id_agent.run if self.id_agent else self.llm_chain
        return agent_runner(formatted_prompt)

    def make_tool(self):
        return Tool(
            name=self.tool_name, description=self.tool_desc, func=self.run_query
        )


### SIMPLE Tool Class #######################


class SimpleTool:
    """
    A simple tool wrapper that encapsulates a callable function within a named tool with a description.

    Attributes:
        tool_name (str): The name of the tool.
        tool_desc (str): A brief description of what the tool does or is used for.
        function (callable): The function that the tool encapsulates. This is the core functionality of the tool.
    """

    def __init__(self, tool_name: str, tool_desc: str, func: callable):
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.function = func

    def make_tool(self):
        """Creates a new instance of the tool with specified attributes."""
        return Tool(name=self.tool_name, description=self.tool_desc, func=self.function)
