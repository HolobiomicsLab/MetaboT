# Quick Start Guide

This guide provides a step-by-step tutorial to help you quickly run and explore MetaboT, our metabolomics analysis tool.

---

## Prerequisites

Before you begin, ensure that you have:

- Completed the [Installation Guide](installation.md)
- Set the necessary environment variables:
  - `OPENAI_API_KEY` (for language model access)
  - `KG_ENDPOINT_URL` (for the knowledge graph endpoint)
- Activated your Python virtual environment

---

## Running a Standard Query

MetaboT includes several predefined queries that demonstrate its capabilities. For example, to run the first standard query (which counts features with matching SIRIUS/CSI:FingerID and ISDB annotations), execute:

```bash
python -m app.core.main -q 1
```

**What this does:**  
- Loads the default configuration and dataset  
- Executes the first query from a list of standard queries  
- Returns insights based on RDF graph analysis

---

## Running a Custom Query

You can also run custom queries tailored to your research needs. For example, to query SIRIUS structural annotations for a specific plant:

```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```

**Note:**  
- Replace the query text in quotes with your desired question.  
- Ensure that the query is relevant to the metabolomics data available in your configuration.

---

## Workflow Overview

MetaboT leverages a multi-agent workflow architecture to process queries efficiently:
 
1. **Entry Agent:**  
   Processes the incoming query and routes it to the appropriate system.
2. **Supervisor Agent:**  
   Oversees and coordinates all processing steps within the workflow.
3. **ENPKG Agent:**  
   Handles domain-specific data processing related to metabolomics.
4. **SPARQL Agent:**  
   Executes queries against the RDF knowledge graph.
5. **Interpreter Agent:**  
   Interprets and formats the query results for user readability.
6. **Validator Agent:**  
   Checks consistency and accuracy of the results.

This modular design allows MetaboT to be extended and customized for various research scenarios.

---

## Example Scenarios

### 1. Basic Feature Analysis

Run a standard query to count LCMS features detected in negative ionization mode:

```bash
python -m app.core.main -c "Count the number of LCMS features in negative ionization mode"
```

### 2. Chemical Structure Analysis

Obtain structural annotations for a plant sample:

```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```

### 3. Bioassay Results Exploration

Examine bioassay data for compounds in a specified extract:

```bash
python -m app.core.main -c "List the bioassay results at 10µg/mL against T.cruzi for lab extracts of Tabernaemontana coffeoides"
```

---

## Interacting with the Knowledge Graph

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

---

## Advanced Configuration

### LangSmith Integration

For enhanced tracking and monitoring of workflow runs:

1. **Set Up LangSmith:**

   ```bash
   export LANGCHAIN_API_KEY="your_api_key_here"
   export LANGCHAIN_PROJECT="MetaboT"
   ```

2. **Review LangSmith logs:**  
   LangSmith will log runtime details that can be used for debugging and auditing query executions.

### Custom Model Settings

Review and adjust the language model configurations in `app/config/params.ini`:

```ini
[llm]
temperature=0.0
id=gpt-4
max_retries=3
```

This ensures that the models used in your workflows are fine-tuned for your specific analysis needs.

---

## Troubleshooting

If you encounter issues, consider the following steps:

- **Environment Variables:**  
  Verify that `OPENAI_API_KEY` and `KG_ENDPOINT_URL` are correctly set.

- **Knowledge Graph Access:**  
  Confirm that the knowledge graph endpoint is reachable and correctly configured in `sparql.ini`.

- **Testing:**  
  Run:
  ```bash
  python app/core/test_db_connection.py
  ```
  to check your database connection.

- **Logs:**  
  Review terminal output for any error messages or warnings during execution.

---

## Next Steps

- **Explore the [User Guide](../user-guide/overview.md)** for in-depth explanations of MetaboT's components.
- **Review the [API Reference](../api-reference/core.md)** to understand function details.
- **Examine the [Examples](../examples/basic-usage.md)** for more advanced usage scenarios.

This refined quick start guide should provide clearer steps and additional details to help you effectively utilize MetaboT.