# IMPORTANT:

**The latest refactored code** is in [https://github.com/holobiomics-lab/kgbot/blob/main/drafts/app/](https://github.com/holobiomics-lab/kgbot/blob/main/drafts/app/).

**The corresponding notebook** is at [https://github.com/holobiomics-lab/kgbot/blob/main/drafts/app/core/LLM_chain_agent.ipynb](https://github.com/holobiomics-lab/kgbot/blob/main/drafts/app/core/LLM_chain_agent.ipynb).

[]
[]
[]

## BELOW IS THE PROTOTYPE (FUNCTIONAL BUT OUTDATED)

## SPARQL-AI-agent

This notebook extracts class properties from a SPARQL endpoint:

```sparql_extracting_classes_properties.ipynb```

This notebook runs the wikibase agent from langchain

```wikibase_agent_demo.ipynb```

This notebook is a multi-tools ReAct prototype using text and vector DB local store, and google web search..

```2305_Langchain_MultiTool_Agent_and_Web.ipynb```

This notebook is a prototype to answer questions from Wikidata with sparql query. It is able to identify keywords in the question and find relevant URIs. 

```Wikidata_Agent_Prototype.ipynb```

Current workbook: This notebook is a prototype to answer questions from ENPKG with sparql queries.

```ENPKG_Prototype.ipynb```

This python file contains classes to build two types of tools. One to generate and run a sparql query given a template. One to generate or load Vector DB embeddings and use a LLM retriever. 

```tools.py```

## KGAI Tool

### Running KGAI
```
from enpkg_agent import run_agent
from enpkg_tools import make_tools

# provide your own OpenAI API key
OPENAI_API_KEY = openai_api_key
endpoint_url = 'https://enpkg.commons-lab.org/graphdb/repositories/ENPKG'

tools = make_tools(endpoint_url=endpoint_url)

# provide your own question
run_agent(question, tools)
```


### Dependencies
conda env export --no-builds | grep -v "^prefix: " > environment.yml
conda env create -f environment.yml


- LangChain
- SPARQLWrapper
- openai
- tiktoken
- chromadb

### Local Files
Three local file needed to run the Agent on ENPKG are stored in the `\local files` directory.

- ENPKG_units.json (stores information about units for numerical literals in ENPKG)
- npc_classes.json (stores URIs of all NPC Classes in ENPKG)
- merged.ttl (schema ttl file for ENPKG constructed with `Constructing Schema.ipynb`)

### Notebooks
**`Constructing Schema.ipynb`**
Notebook with steps to extract all distinct predicates from a KG using a random subsampling technique for large KGs. Also contains steps to construct KG schema as a .ttl file.

**`ENPKG Prototype.ipynb`**
Used as a working notebook to test current prototype of KGAI.

**`ENPKG Unit Testing.ipynb`** 
Notebook that runs KGAI for ENPKG on test questions.

**`Wikidata Prototype.ipynb`**
Prototype to be able to answer natural questions using Wikidata as a SPARQL endpoint. Preliminary.

### Scripts
**`enpkg_agent.py`** 
Script with wrapper function to run the agent.

**`enpkg_tools.py`**
Script with wrapper function to create all ENPKG-specific tools for the agent.

**`prompts.py`**
Contains the main ENPKG agent prompt templates and prompt template for all sub tools.

**`tools.py`**
Contains classes for different types of tools used as the basis for multiple ENPKG-specific tools.

### merged.ttl

The document you've provided is written in the RDF (Resource Description Framework) syntax, specifically using the Turtle serialization format. RDF is a standard model for data interchange on the web and Turtle is one of the human-readable formats to express RDF data. Here's an explanation of its components:

    Prefix Declarations: These are shortcuts for namespaces used throughout the document. For instance, @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> means that rdf is a prefix for the RDF namespace. This makes the rest of the document more readable and concise.

    Ontology and Classes: The owl:Ontology section defines metadata about the ontology (a formal representation of knowledge as a set of concepts and their relationships). Other sections, like enpkg:LabBlank, enpkg:RawMaterial, or enpkg:Annotation, define classes in this ontology. These classes represent concepts in a specific domain.

    Properties: Properties are used to express relationships between things or attributes of things. For example, enpkg:has_lab_process and rdfs:label are properties. In RDF, properties can also be thought of as types of attributes or relationships.

    Instances and Relationships: The document details various instances of the classes and their relationships or attributes. For example, enpkg:RawMaterial enpkg:has_lab_process enpkg:LabExtract states that an instance of RawMaterial has a lab process related to LabExtract.

    Data Types: The document references data types, like xsd:string and xsd:float. These are used to define the types of values that properties can have. xsd is the XML Schema Definition namespace, a way to define the structure and data types for XML documents.

    RDF, RDFS, OWL Constructs: The document uses constructs from RDF, RDFS (RDF Schema), and OWL (Web Ontology Language). These are standards for creating and describing ontologies. They provide ways to define classes, properties, and their relationships.

In summary, this document is an ontology that defines a structured way of representing knowledge about a specific domain. It specifies classes (like RawMaterial, LabBlank), properties (like enpkg:has_lab_process, rdfs:label), and relationships between instances of those classes. This structured representation is crucial for sharing and connecting data on the web in a meaningful way. It enables diverse systems to exchange, understand, and use the information in a consistent manner.
