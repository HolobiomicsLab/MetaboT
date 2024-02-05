# general python libs
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### HELPER FUNCTIONS ################################

### this is not necessary, you can access a nested dict like this :
### dict['key1']['key2']['key3']
def nested_value(data: dict, path: list):
    current = data
    for key in path:
        try:
            current = current[key]
        except:
            return None
    return current

## no need of this function as helper as it is only used in DBRetriever
# def split_data(data, chunk_size = 500, chunk_overlap = 25, seperators = ['PREFIX', '\n\n', '\n', ' ']):
#         text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, 
#                                                                 chunk_overlap=chunk_overlap,
#                                                                 #length_function=tiktoken_len,
#                                                                 separators=seperators
#         )
#         print('Split the documents')
#         split_data = text_splitter.create_documents([str(data)])
#         print (f'You have {len(split_data)} document(s) in your data')

#         OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#         embedding_function = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
#         db = Chroma.from_documents(split_data, embedding_function)
#         return db
    


def count_tokens(content):
    # Initialize Tiktoken with the desired encoding model
    encoding = tiktoken.encoding_for_model("gpt-4")

    # Count the number of tokens in the TTL file
    token_count = len(encoding.encode(content))

    #print(f"The content contains {token_count} tokens.")
    return token_count


### RUN SPARQL QUERY TOOL #####################
## original function
class RunSparql():
    def __init__(self, endpoint: str, tool_name: str, tool_desc: str):
        self.endpoint = endpoint # SPARQL endpoint URL
        self.tool_desc = tool_desc # Description of the tool
        self.tool_name = tool_name # Name of the tool

    def format(self, results):
        formatted_results = [{y:nested_value(z,['value']) for y,z in x.items()}for x in results]
        return formatted_results

    def run_sparql(self, query: str):
        sparql = SPARQLWrapper(self.endpoint) # Create a SPARQLWrapper object
        sparql.setQuery(query) # Set the SPARQL query
        sparql.setReturnFormat(JSON) # Set the return format to JSON
        sparql.setTimeout(600) # Set the timeout for the query execution

        try:
            results = sparql.query().convert() # Execute the SPARQL query and convert the results to JSON
            results = nested_value(results, ['results', 'bindings']) # Retrieve the result bindings from the nested JSON structure
            if len(results) == 0:
                return "No results were found. Please try a different query. Make sure that the logic chains in the query are correct by looking back at the schema"
            
            formatted_results = self.format(results)
            token_count = count_tokens(str(formatted_results))
            if token_count > 3500:
                return f"Results from query are too long and take {token_count} tokens. Run this sparql query manually to get the results to your question."
            else:
                return formatted_results
        except Exception as err:
            return str(err)
            

    def make_tool(self):
        self.tool = Tool(
            name = self.tool_name, # Set the name of the tool
            func=self.run_sparql, # Set the function to be executed for the tool
            description=self.tool_desc # Set the description of the tool
        )

### SPARQL TEMPLATE TOOL ##############################

class QueryTool():
    def __init__(self, template: str, tool_desc: str, tool_name: str, endpoint:str, format_func = None):
        # Initialize the QueryTool object with the given template, tool description, tool name, format function, and SPARQL endpoint
        self.endpoint = endpoint
        self.template = template
        self.tool_desc = tool_desc
        self.tool_name = tool_name
        self.format = format_func
        self.parse_inputs()

    def parse_inputs(self):
        # Parse the input placeholders in the template using regex and store the matches
        pattern = r'(?<!{){([^{}]+)}(?!})'
        self.matches = re.findall(pattern, self.template)

    def get_mapping(self, input_str: str):
        # Map the provided input string to the input placeholders in the template
        self.mapping = {}
        input_str = input_str.split(',')
        for i in range(len(self.matches)):
            self.mapping[self.matches[i]] = input_str[i]
        
                
        # # this do the same as the above
        # dict(zip(self.placeholders, query.split(',')))
        
        return self.lookup(**self.mapping)
    
    def run_sparql(self, query: str):
        # Execute the SPARQL query using the specified endpoint and retrieve the results
        sparql = SPARQLWrapper(self.endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(600)

        results = sparql.query().convert()
        results = nested_value(results, ['results', 'bindings'])

        return results

    def lookup(self, **kwargs):
        # Perform the SPARQL lookup by substituting the placeholders in the template with the provided values
        output = self.run_sparql(self.template.format(**kwargs))
        try:
            if self.format:
                return self.format(output)
            else:
                return output
        except:
            return "Sorry invalid query"
            
    def make_tool(self):
        # Create a Tool object with the specified name, description, and function
        self.tool = Tool(
            name = self.tool_name,
            description = self.tool_desc,
            func = self.get_mapping
        )


### DB Retriever Tool ##########################################################
class DBRetriever():
    def __init__(self, 
                 prompt: str, 
                 filepath: str, 
                 tool_name: str, 
                 tool_desc: str, 
                 parser = None, 
                 chunk_size=500, 
                 chunk_overlap=25):
        # Initialize the DBRetriever object with the provided arguments
        self.prompt = prompt
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.filepath = filepath
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.seperators = ['PREFIX', '\n\n', '\n', ' ']
        if parser:
            self.parser = parser
        else:
            self.parser = self.default_parse
        # you can simplify by : parser or self.default_parse 
        
        ### adding all attributes in init allow to have a good overview of the class
        self.openai_api_key = os.getenv("OPENAI_API_KEY") 
        self.data = None
        self.split_data = None
        self.embeddings = None
        self.db = None
        
    
    def split_data(self):
        # Split the data into chunks using a text splitter
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=self.chunk_size, 
                                                                chunk_overlap=self.chunk_overlap,
                                                                separators=self.seperators
        )
        print('Split the documents')
        self.split_data = text_splitter.create_documents([str(self.data)])
        # Note: If you're using PyPDFLoader then it will split by page for you already
        print(f'You have {len(self.split_data)} document(s) in your data')

        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.db = Chroma.from_documents(self.split_data, self.embeddings)
    
    # more meaningful name, as it do embedding, split and create db
    # too much responsabilities for one method
    #For clarity and maintenance, it's beneficial to split these responsibilities into separate methods.
    # logging instead of print
    
    def default_parse(self, filepath: str):
        # Default parser function to load data from a JSON file
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    ## this is a static method as it does not use any instance variable
    # smplification : return json.load(f)
    
    def get_embeddings(self):
        # Load the data and split it into chunks
        self.data = self.parser(self.filepath)
        self.db = self.split_and_embed()

    def load_embeddings(self, embeddings):
        # Load precomputed document embeddings
        self.db = embeddings

    def make_tool(self, docs=4):
        # Create a tool using the given prompt and retriever
        # self.docs = docs
        llm = ChatOpenAI(
            model_name='gpt-4',
            temperature=0.2,
            max_tokens=1500,
            openai_api_key=self.openai_api_key,
        )
        self.retriever = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type='stuff',
            retriever=self.db.as_retriever(search_kwargs={"k": docs}),
        )

        def prompt_format(string: str):
            # Format the question and retrieve the answer using the retriever
            return self.retriever.run(self.prompt.format(question=string))
        
        self.tool = Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=prompt_format
        )

### SIMPLE AGENT Class #######################

class SimpleAgent():
    def __init__(
        self,
        prompt: str, 
        tool_name: str, 
        tool_desc: str, 
        tools: list,
        parser='simple',
        model='gpt-4'
    ):
        # Initialize instance variables
        self.prompt = prompt
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.tools = tools
        self.parser_type = parser
        self.model = model
    
    ## parsing() and parsing_simple() : theses two functions are very similar, you can merge them into one with a if statement
    def parsing(self, string):
        """
        Parse the string using keyword-question approach.
        """
        
        # The spliting can be a function apart from parsing(), in order to divide responsabilities
        split = string.split(":")
        keyword, question = split[0], ':'.join(split[1:])
        id_prompt = PromptTemplate(
            input_variables=['input', 'question'],
            template=self.prompt
        )
        
        # Instantiate ChatOpenAI agent
        self.llm = ChatOpenAI(temperature=0.8, model=self.model, verbose=True)
    
        # Initialize and run ID agent
        self.id_agent = initialize_agent(self.tools, self.llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)
        return self.id_agent.run(id_prompt.format(input=keyword, question=question))

    
    def parsing_simple(self, string):
        """
        Parse the string using simple approach.
        """
        id_prompt = PromptTemplate(
            input_variables=['input'],
            template=self.prompt
        )
        
        # Instantiate ChatOpenAI agent
        self.llm = ChatOpenAI(temperature=0.8, model=self.model, verbose=True)
        
        if len(self.tools) > 0:
            # Initialize and run ID agent
            self.id_agent = initialize_agent(self.tools, self.llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)
            return self.id_agent.run(id_prompt.format(input=string))
        else:
            # Instantiate LLMChain
            self.llm_chain = LLMChain(llm=self.llm, prompt=id_prompt)
            return self.llm_chain(id_prompt.format(input=string))
    
    def make_tool(self):
        """
        Create the tool based on the specified parser type.
        """
        ## this if / elif statement become unnecessary
        if self.parser_type == 'simple':
            self.parser = self.parsing_simple
        elif self.parser_type == 'keyword_question':
            self.parser = self.parsing
        
        self.tool = Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=self.parser
        )


### SIMPLE Tool Class #######################

class SimpleTool():
    def __init__(self,
            tool_name: str, 
            tool_desc: str, 
            func: callable
    ):
        self.tool_name = tool_name
        self.tool_desc = tool_desc
        self.function = func

    def make_tool(self):
        self.tool = Tool(
            name=self.tool_name,
            description=self.tool_desc,
            func=self.function
        )