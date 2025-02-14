
# MetaboT 🧪 🤖 ✨ 🍵

[![License: MIT](https://img.shields.io/badge/License-MIT-g.svg)]()
[![Arxiv](https://img.shields.io/badge/arXiv-2502.09604-B21A1B)]()
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?logo=huggingface&logoColor=000)]()
[![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?logo=YouTube&logoColor=white)](https://www.youtube.com/@holobiomicslab)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://x.com/HolobiomicLab)
[![Bluesky](https://img.shields.io/badge/Bluesky-0285FF?logo=bluesky&logoColor=fff)](https://bsky.app/profile/holobiomicslab.bsky.social)
[![GitHub Stars](https://img.shields.io/github/holobiomicslab/metabot/SelfCite?style=social)](https://github.com/holobiomicslab/metabot)

## General Information

🤖 MetaboT 🍵 is an AI system that accelerates mass spectrometry-based metabolomics data mining. Leveraging advanced large language models and knowledge graph technologies, MetaboT translates natural language queries into SPARQL requests—enabling researchers to explore and interpret complex metabolomics datasets. Built in Python and powered by state-of-the-art libraries, MetaboT offers an intuitive chat interface that bridges the gap between data complexity and user-friendly access. MetaboT can installed locally and you can try our demo instance on an open [1,600 plant extract dataset](https://doi.org/10.1093/gigascience/giac124) available at [https//metabot.holobiomicslab.cnrs.fr](https//metabot.holobiomicslab.cnrs.fr).

---

## Citation, Institutions & Funding Support

If you use or reference 🤖 MetaboT 🍵 in your research, please cite it as follows:

**MetaboT: A Conversational AI-Agent for Accessible Mass Spectrometry Metabolomics Data Mining**  
*Madina Bekbergenova, et al. DOI.*

[![DOI](https://img.shields.io/badge/DOI-00.0000/arXiv.000.00000-green?color=FF8000?color=009922)]()

**Institutions:**
- Université Côte d'Azur, CNRS, ICN, Nice, France. [See HolobiomicsLab website](https://holobiomicslab.eu) and [![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/holobiomicslab) organization.
- INRIA, Université Côte d’Azur, CNRS, I3S, France. [See WIMMICS website](https://team.inria.fr/wimmics/) and [![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/Wimmics) organization.
- [Interdisciplinary Institute for Artificial Intelligence (3iA) Côte d'Azur, Nice, France](https://3ia.univ-cotedazur.eu/).
- School of Pharmaceutical Sciences, University of Geneva, Switzerland.
- Swiss Institute of Bioinformatics (SIB), Lausanne, Switzerland.

**Funding Support:**  
This work was supported by the French government through the France 2030 investment plan managed by the National Research Agency (ANR), as part of the Initiative of Excellence Université Côte d’Azur (*ANR-15-IDEX-01*) and served as a early prototype for the [MetaboLinkAI](https://www.metabolinkai.net) project (*ANR-24-CE93-0012-01*). This work also benefited from project [*189921*](https://data.snf.ch/grants/grant/189921) funded by the Swiss National Foundation (SNF).

---

### Prepare Your Mass Spectrometry Data
To use 🤖 MetaboT 🍵, your mass spectrometry processing and annotation results must first be represented as a knowledge graph, with the corresponding endpoint deployed. You can utilize the [Experimental Natural Products Knowledge Graph library](https://doi.org/10.1021/acscentsci.3c00800) for this purpose.

By default, MetaboT connects to the public ENPKG endpoint for the ENPKG knowledge graph, which hosts an open and reusable annotated mass spectrometry dataset derived from a chemodiverse collection of 1,600 plant extracts. For further details, please refer to the [associated publication](https://doi.org/10.1093/gigascience/giac124).


### Hardware
- **CPU**: Any modern processor  
- **RAM**: **At least 8GB**  

### Software Requirements
#### OS Requirements
This package has been tested on:
- **macOS**: Sonoma (14.5)  
- **Linux**: Ubuntu 22.04 LTS, Debian 11  

It should also work on other Unix-based systems. For more deets on compatibility, check out [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) if you run into troubles.

---

## Installation Guide 🚀

### Prerequisites

1. **Conda Installation**  
   - Ensure Conda (Anaconda/Miniconda) is installed.  
   - [Conda Installation Docs](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

2. **API Keys**  
   Required API keys:  
   - **OpenAI API Key**: Get it from [OpenAI Platform](https://platform.openai.com/api-keys)  
   - **LangSmith API Key**: Check [LangSmith](https://smith.langchain.com/)  

   > **Disclaimer:** The OpenAI API is a commercial and paid service. Our default model is **gpt-4o**, and its usage will incur costs according to OpenAI's pricing policy.  By default, MetaboT uses gpt-4o.
   > **Data Privacy:** Please note that data submitted to the OpenAI API is subject to OpenAI’s privacy policy. Avoid sending sensitive or confidential information, as data may be logged for quality assurance and research purposes.

   Create a `.env` file in the root directory with your credentials:

   ```bash
   OPENAI_API_KEY=your_openai_key_here
   LANGCHAIN_API_KEY=your_langsmith_key_here
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_PROJECT=metabot_project 


### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/holobiomicslab/MetaboT.git
   git checkout dev
   cd MetaboT
   ```

2. **Create and Activate the Conda Environment**  

   For macOS:
   ```bash
   conda env create -f environment.yml
   conda activate MetaboT
   ```

   For Linux:
   ```bash
   # Update system dependencies first
   sudo apt-get update
   sudo apt-get install -y python3-dev build-essential

   # Then create and activate the conda environment
   conda env create -f environment.yml
   conda activate MetaboT
   ```
   > Pro-tip: If you hit any issues with psycopg2, the `environment.yml` uses `psycopg2-binary` for maximum compatibility.

---

## Application Startup Instructions ▶️
The application is structured as a Python module with dot notation imports—so choose your style, whether absolute (e.g., `app.core.module1.module2`) or relative (e.g., `..core.module1.module2`).

### Demo
To launch the application, use Python's `-m` option. The main entry point is in `app.core.main`:

```bash
cd MetaboT
python -m app.core.main -q 1
```

Expected output includes runtime metrics and a welcoming prompt. 😎

### Running with a Custom Question

```bash
python -m app.core.main -c "Your custom question"
```

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
│   │   │   │   └── tool_fileparser.py
│   │   │   ├── interpreter
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_interpreter.py
│   │   │   ├── sparql
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   ├── tool_merge_results.py
│   │   │   │   ├── tool_sparql.py
│   │   │   │   └── tool_wikidata_query.py
│   │   │   ├── validator
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompt.py
│   │   │   │   └── tool_validator.py
│   │   │   ├── supervisor
│   │   │   │   ├── agent.py
│   │   │   │   └── prompt.py
│   │   │   └── toy_example
│   │   │       ├── agent.py
│   │   │       ├── prompt.py
│   │   │       └── tool_say_hello.py
│   │   ├── graph_management
│   │   │   └── RdfGraphCustom.py
│   │   ├── main.py
│   │   ├── memory
│   │   │   └── custom_sqlite_file.py
│   │   ├── utils.py
│   │   └── workflow
│   │       └── langraph_workflow.py
│   ├── data
│   │   └── submitted_plants.csv
│   │   └── npc_class.csv
│   ├── graphs
│   │   ├── graph.pkl
│   │   └── schema.ttl
│   ├── notebooks
│   ├── ressources
│   └── tests
├── environment.yml
├── environment_alternative.yml
└── langgraph_checkpoint.db
```

---

## Agent Setup Guidelines 🧑‍💻

### Agent Directory Creation
Create a dedicated folder for your agent within the `app/core/agents/` directory. See [here](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents).

### Standard File Structure
- **Agent (`agent.py`)**: Copy from an existing agent unless your tool requires private class property access. Refer to "If Your Tool Serves as an Agent" for special cases.  
  > Psst... don't let the complexities of Python imports overcomplicate your flow—trust the process!

- **Prompt (`prompt.py`)**: Adapt the prompt for your specific context/tasks. Configure the `MODEL_CHOICE`, default is `llm-o` for *gpt-4o* (per `app/config/params.ini`, [see here](https://github.com/holobiomics-lab/MetaboT/blob/main/app/config/params.ini)).

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

**Contributing to 🤖 MetaboT 🍵**

We use the `dev` branch for pushing our contributions [here on GitHub](https://github.com/holobiomicslab/MetaboT/tree/dev). Please create your own branch (either user-centric like `dev_benjamin` or feature-centric like `dev_langgraph`) and submit a pull request to the `dev` branch when you're ready for review. Our AI PR-Agent 🤖 is always standing by to help trigger pull requests and even handle issues smartly—because why not let a smarty pants bot lend a hand?

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

Your contributions make MetaboT awesome! Thank you for being part of our journey and for keeping the code as sharp as your wit. 😎🚀

---

## License

MetaboT is open source and released under the [MIT License](LICENSE). This license allows you to freely use, modify, and distribute the software, provided that you include the original copyright notice and license terms.