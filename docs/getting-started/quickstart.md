
# Quick Start Guide 🚀

Welcome to the Quick Start Guide for MetaboT. This guide will help you quickly run and test the application.

---

## Prerequisites ✅

Before you begin, ensure that you have:

- Completed the [Installation Guide](installation.md)
- Set the necessary environment variables:
  - `OPENAI_API_KEY` (for language model access)
  - `KG_ENDPOINT_URL` (for the knowledge graph endpoint)
- Activated your Python virtual environment


## Running a Standard Query 🔍

MetaboT includes several predefined queries that demonstrate its capabilities. For example, to run the first standard query (which counts features with matching SIRIUS/CSI:FingerID and ISDB annotations), execute:

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

---

## Workflow Overview 🔄

MetaboT leverages a multi-agent workflow architecture to process queries efficiently:

- **Entry Agent:** Processes the incoming query and routes it to the appropriate system.
- **Supervisor Agent:** Oversees and coordinates all processing steps within the workflow.
- **ENPKG Agent:** Handles domain-specific data processing related to metabolomics.
- **SPARQL Agent:** Executes queries against the RDF knowledge graph.
- **Interpreter Agent:** Interprets and formats the query results for user readability.
- **Validator Agent:** Checks consistency and accuracy of the results.


This modular design allows MetaboT to be extended and customized for various research scenarios.

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

MetaboT connects to a knowledge graph to enrich analysis:
```python
from app.core.graph_management.RdfGraphCustom import RdfGraph

# Connect to the knowledge graph using the defined endpoint
graph = RdfGraph(
    query_endpoint="https://enpkg.commons-lab.org/graphdb/repositories/ENPKG",
    standard="rdf"
)
```
Make sure that your `KG_ENDPOINT_URL` environment variable is correctly set to point to your graph database.

## Advanced Configuration ⚙️

### LangSmith Integration

For enhanced tracking and monitoring of workflow runs, we are using [LangSmith](https://www.langchain.com/langsmith). An API key is needed ([free upon registration(]((https://www.langchain.com/langsmith))) and set the .env variable as follow:

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

- **Environment Variables:** Verify that `OPENAI_API_KEY` and `KG_ENDPOINT_URL` are correctly set.
- **Knowledge Graph Access:** Confirm that the knowledge graph endpoint is reachable and correctly configured in [`app/config/sparql.ini`](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/sparql.ini).
- **Testing:** Run `python app/core/test_db_connection.py` to check your database connection.
- **Logs:** Review terminal output for any error messages or warnings during execution.

---
**Next Steps** ➡️

- Explore the User Guide for in-depth explanations of MetaboT's components.
- Review the API Reference to understand function details.
- Examine the Examples for more advanced usage scenarios.
