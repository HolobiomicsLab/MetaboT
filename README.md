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
│   │   ├── config.json
│   │   ├── logging.ini
│   │   ├── logs
│   │   │   ├── app.log
│   │   │   └── app.log.1
│   │   ├── params.ini
│   │   └── sparql.ini
│   ├── core
│   │   ├── agents
│   │   │   ├── agents_factory.py
│   │   │   ├── enpkg
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── substructure_workinprogress.py
│   │   │   │   ├── tool_chemicals.py
│   │   │   │   ├── tool_smiles.py
│   │   │   │   ├── tool_target.py
│   │   │   │   └── tool_taxon.py
│   │   │   ├── entry
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_memory.py
│   │   │   ├── interpreter
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_interpreter.py
│   │   │   ├── sparql
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_sparql.py
│   │   │   ├── supervisor
│   │   │   │   ├── agent.py
│   │   │   │   └── prompt.py
│   │   │   ├── temp_for_record.py
│   │   │   └── tool_interface.py
│   │   ├── graph_management
│   │   │   ├── RdfGraphCustom.py
│   │   ├── main.py
│   │   ├── memory
│   │   │   ├── custom_sqlite_file.py
│   │   │   └── log_search.py
│   │   ├── utils.py
│   │   └── workflow
│   │       └── langraph_workflow.py
│   ├── data
│   ├── graphs
│   │   ├── graph.pkl
│   │   └── schema.ttl
│   ├── notebooks
│   └── tests
├── environment.yml
├── environment_alternative.yml
└── langgraph_checkpoint.db


````

## Development guidelines

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