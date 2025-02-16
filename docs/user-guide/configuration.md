# Configuration Guide 🛠️

This guide details all configuration options available in 🧪 MetaboT 🍵, helping you customize the system to your specific needs.

---
## Configuration Overview 📁

🧪 MetaboT 🍵 uses several configuration files located in the [`app/config/`](app/config/) directory:

- **[`params.ini`](app/config/params.ini)**: Language model configurations
- **[`sparql.ini`](app/config/sparql.ini)**: SPARQL query templates and settings
- **[`logging.ini`](app/config/logging.ini)**: Logging configuration
- **.env**: Environment variables (created by user)

---
## LLMs Configuration 🤖

Located in [`params.ini`](app/config/params.ini), this configuration controls the behavior of different language models used in the system.

```ini
[llm]
id = gpt-4o-2024-08-06
temperature = 0
max_retries = 3

[llm_preview]
id = chatgpt-4o-latest
temperature = 0
max_retries = 3

[llm_o]
id = gpt-4o-2024-08-06
temperature = 0
max_retries = 3

[llm_mini]
id = gpt-4o-mini
temperature = 0
max_retries = 3

[llm_o3_mini]
id = o3-mini-2025-01-31
temperature = 1
max_retries = 3

[llm_o1]
id = o1-2024-12-17
temperature = 1
max_retries = 3

[llm_o1_min]
id = o1-mini-2024-09-12
temperature = 1
max_retries = 3

[llm_o1_min_preview]
id = o1-preview-2024-09-12
temperature = 1
max_retries = 3
```

### Available Sections

- **Main LLM (`[llm]`)**
  Primary language model for complex queries (GPT-4o 2024.08.06)
- **Preview Model (`[llm_preview]`)**
  Latest model versions with cutting-edge capabilities
- **Optimized Model (`[llm_o]`)**
  Production-optimized version of GPT-4o 2024.08.06
- **Mini Model (`[llm_mini]`)**
  Lightweight GPT-4o variant for basic tasks
- **O3 Mini (`[llm_o3_mini]`)**
  Specialized model for experimental tasks (higher creativity)
- **O1 Core (`[llm_o1]`)**
  Advanced model for research and development
- **O1 Mini (`[llm_o1_min]`)**
  Compact version of O1 Core for prototyping
- **O1 Preview (`[llm_o1_min_preview]`)**
  Early access to upcoming O1 model features

Note: 🧪 MetaboT 🍵 supports any OpenAI-compatible API endpoints through custom configurations.

### Parameters

- `id`: Model identifier (e.g., gpt-4, gpt-3.5-turbo)
- `temperature`: Randomness in responses (0-1)
- `max_retries`: Number of retry attempts
- `model_kwargs`: Additional model parameters (optional)

---

## SPARQL Configuration 🔍

The [`sparql.ini`](app/config/sparql.ini) file contains SPARQL query templates and settings for the knowledge graph interaction.

### Query Templates

```ini
[sparqlQueries]
# Class information query
CLS_RDF = SELECT DISTINCT ?cls ?com ?label
        WHERE {
            ?cls a rdfs:Class .
            OPTIONAL { ?cls rdfs:comment ?com }
            OPTIONAL { ?cls rdfs:label ?label }
        }
        GROUP BY ?cls ?com ?label

# Class relationships query
CLS_REL_RDF = SELECT ?property (SAMPLE(COALESCE(?type, STR(DATATYPE(?value)), "Untyped")) AS ?valueType) 
        WHERE {...}
```

### Excluded URIs

```ini
[excludedURIs]
uris = http://www.w3.org/1999/02/22-rdf-syntax-ns#type,
       http://www.w3.org/2000/01/rdf-schema#comment,
       http://www.w3.org/2000/01/rdf-schema#Class,
       http://xmlns.com/foaf/0.1/depiction
```

---
## Logging Configuration 📝

The [`logging.ini`](app/config/logging.ini) file controls the logging behavior of 🧪 MetaboT 🍵.

### Logger Settings

```ini
[loggers]
keys=root

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler
```

### Handler Configuration

- **Console Handler**  
  ```ini
  [handler_consoleHandler]
  class=StreamHandler
  level=INFO
  formatter=simpleFormatter
  args=(sys.stdout,)
  ```
- **File Handler**  
  ```ini
  [handler_fileHandler]
  class=logging.handlers.RotatingFileHandler
  level=INFO
  formatter=detailedFormatter
  args=('./app/config/logs/app.log', 'w', 100000, 5)
  ```

### Formatter Settings

- **Simple Formatter (Console)**  
  ```ini
  [formatter_simpleFormatter]
  format=%(name)s - %(levelname)s - %(message)s
  ```
- **Detailed Formatter (File)**  
  ```ini
  [formatter_detailedFormatter]
  format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
  datefmt=%Y-%m-%d %H:%M:%S
  ```

---
## Environment Variables 🔧

Create a `.env` file in the project root with these variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key

# Knowledge Graph Configuration
KG_ENDPOINT_URL=https://enpkg.commons-lab.org/graphdb/repositories/ENPKG

# LangSmith Configuration (Optional)
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=MetaboT
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

---
## Best Practices 📘

### Language Model Selection
- Use `llm` or `llm_o` for complex queries requiring high accuracy.
- Use `llm_mini` or `llm_o3_mini` for faster, cost-effective operations.
- Consider `llm_o3` or `llm_o1`and its variants for complex questions.
- Use `llm_preview` or `llm_o1_min_preview` to test alternative features.

### Logging Configuration
- Keep the default INFO level for production.
- Use the DEBUG level during development.
- Monitor log file sizes (default 1MB per file, 5 files max).

### SPARQL Optimization
- Review and update excluded URIs as needed.
- Monitor query performance.
- Adjust LIMIT values based on your data size.

### Environment Security
- Never commit the `.env` file to version control.
- Rotate API keys regularly.
- Use different keys for development and production.

---
## Troubleshooting 🚨

### Common Issues

- **Language Model Errors**  
    - Check API key validity.
    - Verify model availability.
    - Review rate limits.

- **Logging Issues**  
    - Ensure write permissions for the log directory.
    - Check disk space.
    - Verify log rotation settings.

- **SPARQL Problems**  
    - Validate endpoint accessibility.
    - Check query syntax.
    - Review timeout settings.

---
## Advanced Configuration 🛠️

### Custom Model Integration

To add a new language model configuration:

1. Add a new section to [`params.ini`](app/config/params.ini):
   ```ini
   [llm_custom]
   id = your-model-id
   temperature = 0
   max_retries = 3
   ```
2. Update the model creation code in [`app/core/main.py`](app/core/main.py).

### Custom Query Templates

Add new SPARQL query templates to [`sparql.ini`](app/config/sparql.ini):

```ini
[sparqlQueries]
YOUR_QUERY_NAME = SELECT ...
```

Refer to the respective component documentation for more detailed information.

---
## Default Dataset and Data Conversion 📊

**Note:**  By default, 🧪 MetaboT 🍵 connects to the public ENPKG endpoint which hosts an open, annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset enables you to explore all features of 🧪 MetaboT 🍵 without the need for custom data conversion immediately. To use 🧪 MetaboT 🍵 on your mass spectrometry data, the processed and annotated results must first be converted into a knowledge graph format using the ENPKG tool. For more details on converting your own data, please refer to the [*Experimental Natural Products Knowledge Graph library*](https://github.com/enpkg) and the [associated publication](https://doi.org/10.1021/acscentsci.3c00800).


- Update the `KG_ENDPOINT_URL` in your **.env** file to point to your custom knowledge graph endpoint.
