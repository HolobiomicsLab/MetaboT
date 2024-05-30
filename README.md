# KGbot dev

## General information

**The main notebook** is at [https://github.com/holobiomics-lab/kgbot/blob/dev/app/core/LLM_chain_agent.ipynb](https://github.com/holobiomics-lab/kgbot/blob/dev/app/core/LLM_chain_agent.ipynb)

We use the ```dev``` branch for pushing our contributions [https://github.com/holobiomics-lab/kgbot/tree/dev](https://github.com/holobiomics-lab/kgbot/tree/dev). Please create your own branch like (either user centric like```dev_benjamin``` or feature centric like ```dev_langgraph```) and do a pull request to the ```dev``` branch when ready for reviewing.

The prototype is in the ```prototype``` branch (frozen) [https://github.com/holobiomics-lab/kgbot/tree/prototype](https://github.com/holobiomics-lab/kgbot/tree/prototype)


## Environment setup

Conda is required for setting up the environment. For installation instructions, see: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
1) Install conda
2) To install the environment from the `environment.yml` file, use the following command:
```sh
conda env create -f environment.yml
```

## Application Startup Instructions

The application has been structured as a module and adheres to the dot notation convention for Python imports. To import a module within the Python script, you can either use an absolute path (e.g., app.core.module1.module2) or a relative import (e.g., ..core.module1.module2).

### Launching the Application

To launch the application, you should utilize the -m option from the Python command line interface. 
The main entry point for the application is located within the main module under app.core.main. Follow the steps below to start the application:

````bash
cd kgbot

python -m app.core.main

````

## Project Structure

````bash
.
├── README.md
├── app
│   ├── config
│   │   ├── langgraph.json
│   │   ├── logging.ini
│   │   ├── logs
│   │   │   ├── app.log
│   │   ├── params.ini
│   │   └── sparql.ini
│   ├── core
│   │   ├── agents
│   │   │   ├── agents_factory.py
│   │   │   ├── enpkg
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_chemicals.py
│   │   │   │   ├── tool_smiles.py
│   │   │   │   ├── tool_target.py
│   │   │   │   └── tool_taxon.py
│   │   │   ├── entry
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_fileparser.py
│   │   │   ├── interpreter
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_interpreter.py
│   │   │   ├── sparql
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_merge_results.py
│   │   │   │   ├── tool_sparql.py
│   │   │   │   └── tool_wikidata_query.py
│   │   │   ├── supervisor
│   │   │   │   ├── agent.py
│   │   │   │   └── prompt.py
│   │   │   └── toy_example
│   │   │       ├── agent.py
│   │   │       ├── prompt.py
│   │   │       └── tool_say_hello.py
│   │   ├── graph_management
│   │   │   ├── RdfGraphCustom.py
│   │   ├── main.py
│   │   ├── memory
│   │   │   └── custom_sqlite_file.py
│   │   ├── utils.py
│   │   └── workflow
│   │       └── langraph_workflow.py
│   ├── data
│   ├── graphs
│   │   ├── graph.pkl
│   │   └── schema.ttl
│   ├── notebooks
│   ├── ressources
│   └── tests
├── environment.yml
├── environment_alternative.yml
└── langgraph_checkpoint.db


````
## Agent Setup guidelines

### Agent Directory Creation
Create a dedicated folder for your agent within the app/core/agents directory. This will serve as the primary repository for all agent-specific files.

### Standard File Structure
The agent folder should include the following files:

#### Agent
    agent.py: This file remains consistent across all agents. You should copy this from an existing agent, unless your tool requires accessing private class properties. For such cases, refer to the section 'If Your Tool Serves as an Agent' for guidance.

    During the agent's construction, the parameters are passed accordingly to what is defined in the agent.py file. Please check if the variables are correctly being defined on the agent_factory.py file.

#### Prompt

    prompt.py: Set the MODEL_CHOICE variable to either llm or llm_preview as per the model hyperparameters defined in app/config/params.ini. Customize the prompt to align with your agent's purpose.

#### Tools
    tool_xxxx.py (optional): Any tool scripts should inherit from the Langchain BaseTool class. Define the necessary class attributes such as name, description, and args_schema. Implement the _run function to execute the tool's functionality. Ensure to define a Pydantic model (class inheriting from BaseModel) for input validation, detailing the type and purpose of each input.

    As for the agent, the tools can constructed with parameters passed dinamically. Please check Interpreter agent and tool for reference. 

### Supervisor Configuration
Modify the supervisor prompt to integrate logic that recognizes and selects your agent. The revised prompt should be updated accordingly.

![alt text](/app/ressources/prompt.png)

### Configuration Updates
Alter the app/config/laggraph.json file to incorporate your agent into the application's workflow, ensuring it is recognized as part of the operational sequence.

![alt text](/app/ressources/image.png)

### If Your Tool Serves as an Agent

If your tool functions as an agent, particularly in scenarios requiring interaction with a LLM, specific class properties must be utilized. For an example, see the implementation in app/core/agents/sparql/tool_sparql.py.

Additional class attributes may be necessary to allow use of LLM, extending beyond the basic attributes inherited from BaseTool. This includes defining theses within the init(), ands in the class attributes. Also, you should modify the agent.py file to incorporate instances of these properties through the import_tools() function. Review the tool_parameters variable in app/core/agents/sparql/agent.py for details.



## Development Guidelines

To ensure that all contributors are aligned and to facilitate smoother integration of our work, we kindly ask that you adhere to the following guidelines:

**Documentation Standards**
- **Google Docstring Format**: All documentation for classes and functions should be written following the Google Docstring format. This format is both natural language and supports automatic documentation generation tools. The documentation is also parsed by the LLM to know about class/function signature, so natural language is more indicated.

- **Mintlify Doc Writer for VSCode**: To simplify the process of writing docstrings, we recommend using the Mintlify Doc Writer extension available in Visual Studio Code. This tool automates the creation of docstrings. To use this extension effectively:
    Install Mintlify Doc Writer from the VSCode extensions marketplace.
    In the extension's settings, set the docstring format to Google.
    To generate a docstring for a class or function, simply right-click on the code element and select the Generate Documentation option.
    Review and adjust the generated docstrings as necessary to accurately reflect the code’s purpose and behavior.

**Code Formatting**

To maintain a unified code style across our project, we adhere to the PEP8 convention. This style guide helps in keeping our code readable and maintainable. Here's how to ensure your code meets these standards:

- **Black Formatter** in VSCode: The easiest way to format your code according to PEP8 is by using the Black Formatter extension in Visual Studio Code. Here’s how to use it:
    Install Black Formatter from the VSCode extensions marketplace.
    Right-click inside any Python file and select Format Document to automatically format your code.

  ### Good practices with keys

  As good practive with keys, to further isolate and later facilitate the deployment with online plataforms, please provide the keys as parameters and don't use environmental variables as those are not scalable for production. 


## Logging guidelines

These guidelines will help us efficiently track application behavior, debug issues, and understand application flow.

**Configuration**

Our logging configuration is centralized in an INI file located at app/config/logging.ini. This setup allows us to manage logging behavior across all scripts from a single location.


**Integrating Logging into Your Scripts**

To leverage logging setup, please incorporate the following code at the beginning of each Python script:

```python
from pathlib import Path
import logging.config

# Determine the path to the logging configuration file if your file is in /core
parent_dir = Path(__file__).parent.parent
config_path = parent_dir / "config" / "logging.ini"

# Configure logging based on the specified INI file
logging.config.fileConfig(config_path, disable_existing_loggers=False)

# Create a logger object for the current module
logger = logging.getLogger(__name__)

```

**Usage Recommendations**

**Prefer Logging Over Print**: For any output meant for debugging or information tracking, use the logger object instead of the print function. 

**Logging Levels**: Please use the appropriate level when emitting log messages:
- logger.DEBUG: Detailed information, typically of interest only when diagnosing problems.
- logger.INFO: Confirmation that things are working as expected.
- logger.WARNING: Indicates a deviation from the norm but doesn't prevent the program from working
- logger.ERROR: Issues that prevent certain functionalities from operating correctly but do not necessarily affect the overall application's ability to run.
- logger.CRITICAL: These are used for errors that require immediate attention, such as a complete system failure or a critical resource unavailability.

**Logs Outputs**

Our configuration supports outputting log messages to two destinations:

- Console: Log messages at the INFO level and above will be outputted to the console. This setup is intended for general monitoring and quick diagnostics.
- File: A more detailed log, including messages at the DEBUG level and above, is written to a file. 

The log files are located within the app/config/logs directory. 
