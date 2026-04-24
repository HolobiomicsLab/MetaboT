![Hero Background](docs/assets/images/hero-bg.png)
![MetaboT Logo](assets/logo.png)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?logo=huggingface&logoColor=000)]()
[![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?logo=YouTube&logoColor=white)](https://www.youtube.com/@holobiomicslab)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://x.com/Holobiomicslab)
[![Bluesky](https://img.shields.io/badge/Bluesky-0285FF?logo=bluesky&logoColor=fff)](https://bsky.app/profile/holobiomicslab.bsky.social)
[![GitHub Stars](https://img.shields.io/github/holobiomicslab/metabot/SelfCite?style=social)](https://github.com/holobiomicslab/metabot)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://holobiomicslab.github.io/MetaboT/)

## General Information

Take a break, brew a cup of tea while 🧪 MetaboT 🍵 digs into mass spec data!

🧪 MetaboT 🍵 is an AI system that accelerates mass spectrometry-based metabolomics data mining. Leveraging advanced large language models and knowledge graph technologies, 🧪 MetaboT 🍵 translates natural language queries into SPARQL requests—enabling researchers to explore and interpret complex metabolomics datasets. Built in Python and powered by state-of-the-art libraries, 🧪 MetaboT 🍵 offers an intuitive chat interface that bridges the gap between data complexity and user-friendly access. 🧪 MetaboT 🍵 can be installed locally and you can try our demo instance on an open [1,600 plant extract dataset](https://doi.org/10.1093/gigascience/giac124) available at [ https://metabot.holobiomicslab.eu]( https://metabot.holobiomicslab.eu).

Take a break, brew a cup of tea 🍵, and have some fun with words while 🧪 MetaboT 🍵 digs into mass spec data! Enjoy your brew and happy puzzling!

## v1.1.0 Highlights

- Hardened the interpreter path by isolating LLM-generated Python behind trusted-mode controls and a subprocess runner instead of in-process execution.
- Improved CLI safety with better file staging validation, collision handling, session-scoped logging, and consistent `--api-key` propagation through fallback SPARQL paths.
- Made the Streamlit app easier to launch locally by stabilizing its import path handling and aligning the recommended startup command with the tested repo-root workflow.

## Documentation

Comprehensive documentation is available at [https://holobiomicslab.github.io/MetaboT/](https://holobiomicslab.github.io/MetaboT/). It includes:

- **Installation and Quick Start Guides**
- **User Guide** with configuration details
- **API Reference** for core components, agents, and graph management
- **Usage Examples** for both basic and advanced scenarios
- **Contributing Guidelines**

The documentation is automatically built and deployed using GitHub Actions on every push to the main branch.

To preview and build the documentation locally:

```bash
# Install the required dependencies
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python

# To serve documentation locally, run:
mkdocs serve

# To build the documentation, run:
mkdocs build
```

---

## Citation, Institutions & Funding Support
If you use or reference 🧪 MetaboT 🍵 in your research, please cite it as follows:

**🧪 MetaboT 🍵: An LLM-based Multi-Agent Framework for Interactive Analysis of Mass Spectrometry Metabolomics Knowledge**  
*Madina Bekbergenova, Lucas Pradi, Benjamin Navet, Emma Tysinger, Matthieu Feraud, Yousouf Taghzouti, Martin Legrand, Tao Jiang, Franck Michel, Yan Zhou Chen, Soha Hassoun, Olivier Kirchhoffer, Jean-Luc Wolfender, Florence Mehl, Marco Pagni, Wout Bittremieux, Fabien Gandon, Louis-Félix Nothias. PREPRINT (Version 1) available at Research Square*
[![DOI](https://img.shields.io/badge/DOI-10.21203/rs.3.rs--6591884/v1-green?color=FF8000)](https://doi.org/10.21203/rs.3.rs-6591884/v1)

**Institutions:**
- Université Côte d'Azur, CNRS, ICN, Nice, France
- Interdisciplinary Institute for Artificial Intelligence (3iA) Côte d'Azur, Sophia-Antipolis, France
- Department of Computer Science, University of Antwerp, Antwerp, Belgium
- Department of Electrical Engineering and Computer Science, MIT, Cambridge, MA, USA
- INRIA, Université Côte d'Azur, CNRS, I3S, France
- Department of Computer Science, Tufts University, Medford, MA 02155, USA
- Department of Chemical and Biological Engineering, Tufts University, Medford, MA 02155, USA
- Institute of Pharmaceutical Sciences of Western Switzerland, University of Geneva, Centre Médical Universitaire, Geneva, Switzerland
- School of Pharmaceutical Sciences, University of Geneva, Centre Médical Universitaire, Geneva, Switzerland
- Swiss Institute of Bioinformatics (SIB), Lausanne, Switzerland

**Lab Websites:**
- [HolobiomicsLab](https://holobiomicslab.eu) [![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/holobiomicslab)
- [WIMMICS](https://team.inria.fr/wimmics/) [![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/Wimmics)
- [3iA Côte d'Azur](https://3ia.univ-cotedazur.eu/)

**Funding Support:**  
This work was supported by the French government through the France 2030 investment plan managed by the National Research Agency (ANR), as part of the Initiative of Excellence Université Côte d'Azur (*ANR-15-IDEX-01*) and served as an early prototype for the [MetaboLinkAI](https://www.metabolinkai.net) project (*ANR-24-CE93-0012-01*). This work also benefited from project [*189921*](https://data.snf.ch/grants/grant/189921) funded by the Swiss National Foundation (SNF).

---

## Prepare Your Mass Spectrometry Data

To use 🧪 MetaboT 🍵, your mass spectrometry processing and annotation results must first be represented as a knowledge graph, with the corresponding endpoint deployed. You can utilize the [Experimental Natural Products Knowledge Graph library](https://doi.org/10.1021/acscentsci.3c00800) for this purpose. See the [ENPKG repository](https://github.com/enpkg)

By default, 🧪 MetaboT 🍵 connects to the public ENPKG endpoint for the ENPKG knowledge graph, which hosts an open and reusable annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. For further details, please refer to the [associated publication](https://doi.org/10.1093/gigascience/giac124).

---

## Hardware

- **CPU**: Any modern processor  
- **RAM**: **At least 8GB**

## Software Requirements

#### OS Requirements

This package has been tested on:
- **macOS**: Sonoma (14.5)  
- **Linux**: Ubuntu 22.04 LTS, Debian 11

It should also work on other Unix-based systems. For more details on compatibility, check out [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) if you run into troubles.

---

## Installation Guide 🚀

### Prerequisites

1. **Conda Installation**  
   - Ensure Conda (Anaconda/Miniconda) is installed.  
   - [Conda Installation Docs](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

2. **API Keys**
   Required API keys:
   - Get an API key for your chosen language model:
     - **OpenAI API Key**: Get it from [OpenAI Platform](https://platform.openai.com/api-keys)
     - **DeepSeek API Key**: Get it from DeepSeek
     - **Claude API Key**: Get it from Anthropic
     - Or other models supported by [LiteLLM](https://docs.litellm.ai/docs/providers)

   > **Disclaimer:** Most LLM APIs are commercial and paid services. Our default model is **gpt-4o**, and its usage will incur costs according to the provider's pricing policy.
   >
   > **Data Privacy:** Please note that data submitted to LLM APIs is subject to their respective privacy policies. Avoid sending sensitive or confidential information, as data may be logged for quality assurance and research purposes.

   Optional API keys:
   - **LangSmith API Key**: This is used to see the interactions traces [LangSmith](https://smith.langchain.com/). This is free.

   Create a `.env` file in the root directory with your credentials:

   ```bash
   OPENAI_API_KEY=your_openai_key_here
   LANGCHAIN_API_KEY=your_langsmith_key_here
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_PROJECT=metabot_project 
   ```
   **Note:** The system can also be used with other LLM models, namely: Meta-Llama-3_1-70B-Instruct and deepseek-reasoner. For Meta-Llama-3_1-70B-Instruct (which runs on OVH Cloud – see [OVH Cloud](https://www.ovh.com/)), add the API key OVHCLOUD_API_KEY to your `.env` file; for deepseek-reasoner, add DEEPSEEK_API_KEY. Detailed information on how to configure other LLM models is available [here](https://holobiomicslab.github.io/MetaboT/getting-started/installation/#adding-new-models). Currently, all agents use the OpenAI model gpt-4o (including the SPARQL generation chain). Furthermore, if the initial query yields no results, a SPARQL improvement chain using the OpenAI o3-mini model is activated.

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/holobiomicslab/MetaboT.git
   cd MetaboT
   git checkout dev
   ```

2. **Create and Activate the Conda Environment**  

   For macOS:
   ```bash
   conda env create -f environment.yml
   conda activate metabot
   ```

   For Linux:
   ```bash
   # Update system dependencies first
   sudo apt-get update
   sudo apt-get install -y python3-dev build-essential
  
   # Then create and activate the conda environment
   conda env create -f environment.yml
   conda activate metabot
   ```

    For Windows (using WSL):

   Install WSL if you haven't already:

      ```bash
      wsl --install
      ```
      
   Open WSL and install the required packages:

      ```bash
      sudo apt-get update
      sudo apt-get install -y python3-dev build-essential
      ```
      
   Install Miniconda in WSL:

      ```bash
      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      bash Miniconda3-latest-Linux-x86_64.sh
      source ~/.bashrc
      ```
      
   Create and activate the conda environment:
      ```bash
      conda env create -f environment.yml
      conda activate MetaboT
      ``` 
     
 > Pro-tip: If you hit any issues with psycopg2, the `environment.yml` uses `psycopg2-binary` for maximum compatibility.

---

## Application Startup Instructions ▶️

The application is structured as a Python module with dot notation imports—so choose your style, whether absolute (e.g., `app.core.module1.module2`) or relative (e.g., `..core.module1.module2`).

### Demo

To launch the application, use Python's `-m` option. The main entry point is in `app.core.main`.

To try one of the [standard questions](app/data/standard_questions.txt), run the following command:
 
```bash
cd MetaboT
python -m app.core.main -q 1
```
Here, the number following `-q` specifies the question number from the standard questions which can be viewed in `app/data/standard_questions.txt`.
Expected output includes runtime metrics and a welcoming prompt. 😎

### Running with a Custom Question

```bash
python -m app.core.main -c "Your custom question"
```
### Running via Streamlit

To launch the application through Streamlit, install the dependencies and run the app from the repository root. In your terminal, execute:

```bash
pip install -r requirements.txt
python -m streamlit run streamlit_webapp/streamlit_app.py
```

This repo-root launch path is the recommended setup for local development and matches the Streamlit smoke-tested workflow used in `v1.1.0`. You can provide your OpenAI key in the sidebar once the app starts, or preconfigure contributor/admin keys through environment variables if you use those deployment paths.

---
### Running in Docker

If you prefer to run the application in a containerized environment, Docker support is provided. Make sure Docker and docker-compose are installed on your system.

#### Building the Docker Image

To build the Docker image, run:

```bash
docker-compose build
```

#### Running the Application

To launch the application and run the first standard question, execute:

```bash
docker-compose run metabot python -m app.core.main -q 1
```

This command will start the container, run the application inside Docker, and process the first standard question from [app/data/standard_questions.txt]. You can adjust parameters as needed.

---

## Project Structure

```bash
.
├── README.md
├── app
│   ├── config
│   │   ├── langgraph.json
│   │   ├── logging.ini
│   │   ├── logs
│   │   │   └── app.log
│   │   ├── params.ini
│   │   └── sparql.ini
│   ├── core
│   │   ├── agents
│   │   │   ├── agents_factory.py
│   │   │   ├── enpkg
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_chemicals.py
│   │   │   │   ├── tool_smiles.py
│   │   │   │   ├── tool_target.py
│   │   │   │   └── tool_taxon.py
│   │   │   ├── entry
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_filesparser.py
│   │   │   ├── interpreter
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_interpreter.py
│   │   │   │   └── tool_spectrum.py  
│   │   │   ├── sparql
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_merge_result.py
│   │   │   │   ├── tool_sparql.py
│   │   │   │   └── tool_wikidata_query.py
│   │   │   ├── validator
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_validator.py
│   │   │   └── supervisor
│   │   │       ├── agent.py
│   │   │       └── prompt.py
│   │   ├── graph_management
│   │   │   └── RdfGraphCustom.py
│   │   ├── main.py
│   │   ├── memory
│   │   │   ├── custom_sqlite_file.py
│   │   │   ├── database_manager.py
│   │   │   ├── test_db_connection.py
│   │   │   └── tools_database.py
│   │   ├── utils.py
│   │   └── workflow
│   │   │    └── langraph_workflow.py
│   │   ├── tests
│   │   │    ├── evaluation.py
│   │   │    └── test_utils.py
│   ├── data
│   │   ├── submitted_plants.csv
│   │   ├── npc_class.csv
│   │   └── evaluation_dataset.csv
│   ├── graphs
│   │   ├── graph.pkl
│   │   └── schema.ttl
│   └── notebooks
├── docs
│    ├── api-reference
│    ├── assets
│    ├── examples
│    ├── getting-started
│    ├── user-guide
│    ├── contributing.md
│    └── index.md
├── streamlit_webapp
│   ├── streamlit_app.py
│   └── streamlit_utils.py
├── environment.yml
├── mkdocs.yml
└── requirements.txt
```

---

## Agent Setup Guidelines 🧑‍💻

### Agent Directory Creation
Create a dedicated folder for your agent within the `app/core/agents/` directory. See [here](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents).

### Standard File Structure
- **Agent (`agent.py`)**: Copy from an existing agent unless your tool requires private class property access. Refer to "If Your Tool Serves as an Agent" for special cases.  
  > Psst... don't let the complexities of Python imports overcomplicate your flow—trust the process!

- **Prompt (`prompt.py`)**: Adapt the prompt for your specific context/tasks. Configure the `MODEL_CHOICE`, default is `llm-o` for *gpt-4o* (per [`app/config/params.ini`](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/params.ini)).

- **Tools (`tool_xxxx.py`)** (optional): Inherit from the LangChain `BaseTool`, defining:
  - `name`, `description`, `args_schema`
  - A Pydantic model for input validation
  - The `_run` method for execution

### Supervisor Configuration
Modify the supervisor prompt (see [supervisor prompt](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/supervisor/prompt.py)) to detect and select your agent. Our AI PR-Agent 🤖 is triggered automatically through issues and pull requests, so you'll be in good hands!

### Configuration Updates
Update `app/config/langgraph.json` to include your agent in the workflow. For reference, see [langgraph.json](https://github.com/holobiomicslab/MetaboT/tree/main/app/config/langgraph.json).

### If Your Tool Serves as an Agent
For LLM-interaction, make sure additional class properties are set in `agent.py` (refer to [tool_sparql.py](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/tool_sparql.py) and [agent.py](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/agent.py)). Keep it snazzy and smart!

---

## Development Guidelines

**Contributing to 🧪 MetaboT 🍵**

We use the `dev` branch for pushing our contributions [here on GitHub](https://github.com/holobiomicslab/MetaboT/tree/dev). Please create your own branch (either user-centric like `dev_benjamin` or feature-centric like `dev_langgraph`) and submit a pull request to the `dev` branch when you're ready for review. Our AI PR-Agent 🤖 is always standing by to help trigger pull requests and even handle issues smartly—because why not let a smarty pants bot lend a hand.

**Documentation Standards**
- Use **Google Docstring Format**  
- Consider the **Mintlify Doc Writer for VSCode** for automatically stylish and precise docstrings.

**Code Formatting**
- Stick to **PEP8**
- Leverage the **Black Formatter** for a neat, uniform style.

> Because code deserves to look as sharp as your ideas. 😎

### Good Practices with Keys
Pass keys as parameters instead of environment variables for scalable production deployments.

---

## Logging Guidelines

Centralized logging resides in `app/config/logging.ini`. See [here](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/logging.ini).

Use the following snippet at the start of your Python scripts:
```python
from pathlib import Path
import logging.config

parent_dir = Path(__file__).parent.parent
config_path = parent_dir / "config" / "logging.ini"
logging.config.fileConfig(config_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
```
*Pro-tip:* Use `logger` over `print` for more elegant and traceable output.

---

## Additional Resources

- Explore the ENPKG project on GitHub: [https://github.com/enpkg](https://github.com/enpkg)
- Visit the HolobiomicsLab GitHub organization: [https://github.com/holobiomicslab](https://github.com/holobiomicslab)
- Access the detailed 🧪 MetaboT 🍵 documentation at: [https://holobiomicslab.github.io/MetaboT/](https://holobiomicslab.github.io/MetaboT/)

---

## Contributing 🤝

We warmly welcome your contributions! Here's how to dive in:

1. **Fork & Clone**  
   - Fork the repo on [GitHub](https://github.com/holobiomicslab/MetaboT) and clone your fork.
2. **Create a Feature Branch**
   - Branch from `dev` (e.g., `dev_your_branch_name`).
3. **Develop Your Feature**
   - Write clean code with clear documentation (Google Docstring format is preferred).
   - Our AI PR-Agent 🤖 automatically kicks in when you raise an issue or a pull request.
4. **Commit**
   - Use atomic commits with present-tense messages:
     ```bash
     git commit -m "Add new agent for processing chemical data"
     ```
   - That's the secret sauce to a smooth GitHub PR journey!
5. **Submit a Pull Request**
   - Push your changes and create a PR against the `dev` branch. Fill out all necessary details, including links to related issues (e.g., [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues)).

### Pull Request Process
- Update documentation, run tests, and ensure your code is formatted.  
- The AI PR-Agent is active and will provide first-line feedback!

### Code Quality Guidelines
- Write meaningful tests.
- Maintain rich inline documentation.
- Adhere to PEP8 and best practices.

### Reporting Issues
For bug reports or feature requests, please use our [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) page.

---

Your contributions make 🧪 MetaboT 🍵 awesome! Thank you for being part of our journey and for keeping the code as sharp as your wit. 😎🚀

---

## License

🧪 MetaboT 🍵 is open source and released under the [Apache License 2.0](LICENSE.txt). This license allows you to freely use, modify, and distribute the software, provided that you include the original copyright notice and license terms.

---

## ☕ 🧪 MetaboT 🍵 Tea Time Word Game 🍵

Take a break, brew a cup of tea, and have some fun with words while 🧪 MetaboT 🍵 digs into mass spec data!

Here's a little puzzle to steep your brain:

1. Unscramble the letters in *t-e-a-m-o-b-o-t* to reveal the secret spice behind our data wizard!
2. What do you get when you mix a hot cup of tea with a powerful AI? Absolutely *tea-rific* insights!

Remember: While you relax with your favorite treat, 🧪 MetaboT 🍵 is busy infusing data with meaning. Sip, smile, and let the insights steep into brilliance!

Enjoy your brew and happy puzzling!
