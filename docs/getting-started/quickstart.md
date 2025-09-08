# Quick Start Guide 🚀

Welcome to the Quick Start Guide for 🧪 MetaboT 🍵. This guide will help you quickly run and test the application.

👉 **Try the MetaboT Web App Demo**: [https://metabot.holobiomicslab.eu](https://metabot.holobiomicslab.eu) — no installation needed!  

The demo provides access to an open [dataset of 1,600 plant extracts](https://doi.org/10.1093/gigascience/giac124). You can explore metabolomics data and ask questions about the dataset directly through the web interface.

---

## Prerequisites ✅ (For Local Installation)

Before you begin, ensure that you have:

- Completed the [Installation Guide](installation.md)

- Set the necessary environment variables in your `.env` file:

    - API key for your chosen language model:
         - `OPENAI_API_KEY` if using OpenAI
         - `DEEPSEEK_API_KEY` if using DeepSeek
        - `CLAUDE_API_KEY` if using Claude

    -  SPARQL endpoint configuration:
         - `KG_ENDPOINT_URL` (required)
        - `SPARQL_USERNAME` and `SPARQL_PASSWORD` (if your endpoint requires authentication)
    
- Activated your Python virtual environment


## Running a Standard Query 🔍

🧪 MetaboT 🍵 includes several predefined queries that demonstrate its capabilities. Those questions could be found [here](https://github.com/HolobiomicsLab/MetaboT/blob/dev_madina/app/data/standard_questions.txt). For example, to run the first standard query (which counts features with matching SIRIUS/CSI:FingerID and ISDB annotations), execute:

```bash
python -m app.core.main -q 1
```

**What this does:**  
- Loads the default configuration and dataset  
- Executes the first query from a list of standard queries  
- Returns insights based on RDF graph analysis


## Running a Custom Query 🛠️

You can also run custom queries tailored to your research needs. For example, to query SIRIUS structural annotations for a specific plant:
```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```
**Note:**  
- Replace the query text in quotes with your desired question.  
- Ensure that the query is relevant to the metabolomics data available in your configuration.

## Running in Docker 🐳

If you prefer to run 🧪 MetaboT within a Docker container, follow these steps:

1. **Build the Docker Image:**
  Ensure Docker and docker-compose are installed, then run:
  ```bash
  docker-compose build
  ```

2. **Run the Application in Docker:**
  To execute the first standard query, run:
  ```bash
  docker-compose run metabot python -m app.core.main -q 1
  ```
  This command starts the container and runs the application accordingly. You can adjust the command as needed.

---

## Workflow Overview 🔄

🧪 MetaboT 🍵 leverages a multi-agent workflow architecture to process queries efficiently:

- **Entry Agent:** Processes the incoming query and routes it to the appropriate system.
- **Validator Agent:** Immediately verifies that the incoming query is pertinent to the knowledge graph, ensuring its alignment with domain-specific schema.
- **Supervisor Agent:** Oversees and coordinates all processing steps within the workflow.
- **ENPKG Agent:** Handles domain-specific data processing related to metabolomics.
- **SPARQL Agent:** Generates and executes queries against the RDF knowledge graph.
- **Interpreter Agent:** Interprets and formats the query results for user readability.


This modular design allows 🧪 MetaboT 🍵 to be extended and customized for various research scenarios.

---

## Example Scenarios 📚

### Basic Feature Analysis
Run a standard query to count LCMS features detected in negative ionization mode:
```bash
python -m app.core.main -c "Count the number of LCMS features in negative ionization mode"
```

### Chemical Structure Analysis
Obtain structural annotations for a plant sample:
```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```

### Bioassay Results Exploration
Examine bioassay data for compounds in a specified extract:
```bash
python -m app.core.main -c "List the bioassay results at 10µg/mL against T.cruzi for lab extracts of Tabernaemontana coffeoides"
```

## Interacting with the Knowledge Graph 🌐

🧪 MetaboT 🍵 connects to a knowledge graph to enrich analysis:
```python
import os
from app.core.graph_management.RdfGraphCustom import RdfGraph

# Connect to the knowledge graph using the defined endpoint
# If SPARQL_USERNAME and SPARQL_PASSWORD environment variables are set,
# they will be automatically used for authentication
graph = RdfGraph(
    query_endpoint="https://enpkg.commons-lab.org/graphdb/repositories/ENPKG",
    standard="rdf",
    auth=None  # Will automatically use environment variables if available
)

# Or explicitly provide authentication:
auth = (os.getenv("SPARQL_USERNAME"), os.getenv("SPARQL_PASSWORD"))
graph = RdfGraph(
    query_endpoint="your_endpoint_url",
    standard="rdf",
    auth=auth
)
```
Make sure that your `KG_ENDPOINT_URL` environment variable is correctly set to point to your graph database.

## Advanced Configuration ⚙️

### LangSmith Integration

For enhanced tracking and monitoring of workflow runs, we are using [LangSmith](https://docs.smith.langchain.com/). An API key is needed ([free upon registration](https://www.langchain.com/langsmith)) and set the .env variable as follow:

1. Set up LangSmith:
    ```bash
    export LANGCHAIN_API_KEY="your_api_key_here"
    export LANGCHAIN_PROJECT="MetaboT"
    ```
2. Review LangSmith logs to access runtime details for debugging and auditing.

### Custom Model Settings

Review and adjust the language model configurations in [`app/config/params.ini`](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/params.ini):
```ini
[llm]
temperature=0.0
id=gpt-4
max_retries=3
```
This ensures that the models used in your workflows are fine-tuned for your specific analysis needs.

## Troubleshooting 🐞

If you encounter issues, consider the following steps:

- **Environment Variables:** Verify that your chosen LLM API key (`OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `CLAUDE_API_KEY`, etc.) and `KG_ENDPOINT_URL` are correctly set in your `.env` file.
- **Knowledge Graph Access:** Confirm that the knowledge graph endpoint is reachable and correctly configured.
- **Logs:** Review terminal output for any error messages or warnings during execution.

---
**Next Steps** ➡️

- Explore the User Guide for in-depth explanations of 🧪 MetaboT 🍵's components.
- Review the API Reference to understand function details.
- Examine the Examples for more advanced usage scenarios.
