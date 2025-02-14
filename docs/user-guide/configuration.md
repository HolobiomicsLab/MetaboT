# Configuration Guide

This guide details all configuration options available in MetaboT, helping you customize the system to your specific needs.

## Configuration Files Overview

MetaboT uses several configuration files located in the `app/config/` directory:

- `params.ini`: Language model configurations
- `sparql.ini`: SPARQL query templates and settings
- `logging.ini`: Logging configuration
- `.env`: Environment variables (created by user)

## Language Model Configuration

Located in `params.ini`, this configuration controls the behavior of different language models used in the system.

```ini
[llm]
id = gpt-4o
temperature = 0
max_retries = 3
```

### Available Sections

1. **Main LLM (`[llm]`)**
   - Primary language model for complex queries
   - Recommended for most operations

2. **Preview Model (`[llm_preview]`)**
   - Latest model versions
   - Used for testing new features

3. **Optimized Model (`[llm_o]`)**
   - Balanced performance and cost
   - Suitable for production use

4. **GPT-3.5 Model (`[llm_3_5]`)**
   - Faster, more economical option
   - Good for simpler queries

5. **Mini Model (`[llm_mini]`)**
   - Lightweight version
   - Useful for development and testing

### Parameters

- `id`: Model identifier (e.g., gpt-4, gpt-3.5-turbo)
- `temperature`: Randomness in responses (0-1)
- `max_retries`: Number of retry attempts
- `model_kwargs`: Additional model parameters (optional)

## SPARQL Configuration

The `sparql.ini` file contains SPARQL query templates and settings for the knowledge graph interaction.

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

## Logging Configuration

The `logging.ini` file controls the logging behavior of MetaboT.

### Logger Settings

```ini
[loggers]
keys=root

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler
```

### Handler Configuration

1. **Console Handler**
   ```ini
   [handler_consoleHandler]
   class=StreamHandler
   level=INFO
   formatter=simpleFormatter
   args=(sys.stdout,)
   ```

2. **File Handler**
   ```ini
   [handler_fileHandler]
   class=logging.handlers.RotatingFileHandler
   level=INFO
   formatter=detailedFormatter
   args=('./app/config/logs/app.log', 'w', 100000, 5)
   ```

### Formatter Settings

1. **Simple Formatter (Console)**
   ```ini
   [formatter_simpleFormatter]
   format=%(name)s - %(levelname)s - %(message)s
   ```

2. **Detailed Formatter (File)**
   ```ini
   [formatter_detailedFormatter]
   format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
   datefmt=%Y-%m-%d %H:%M:%S
   ```

## Environment Variables

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

## Configuration Best Practices

1. **Language Model Selection**
   - Use `llm` for complex queries requiring high accuracy
   - Use `llm_3_5` for simpler queries to optimize costs
   - Consider `llm_mini` for development and testing

2. **Logging Configuration**
   - Keep default INFO level for production
   - Use DEBUG level during development
   - Monitor log file sizes (default 1MB per file, 5 files max)

3. **SPARQL Optimization**
   - Review and update excluded URIs as needed
   - Monitor query performance
   - Adjust LIMIT values based on your data size

4. **Environment Security**
   - Never commit `.env` file to version control
   - Rotate API keys regularly
   - Use different keys for development and production

## Troubleshooting

### Common Issues

1. **Language Model Errors**
   - Check API key validity
   - Verify model availability
   - Review rate limits

2. **Logging Issues**
   - Ensure write permissions for log directory
   - Check disk space
   - Verify log rotation settings

3. **SPARQL Problems**
   - Validate endpoint accessibility
   - Check query syntax
   - Review timeout settings

## Advanced Configuration

### Custom Model Integration

To add a new language model configuration:

1. Add a new section to `params.ini`:
   ```ini
   [llm_custom]
   id = your-model-id
   temperature = 0
   max_retries = 3
   ```

2. Update the model creation code in `app/core/main.py`

### Custom Query Templates

Add new SPARQL query templates to `sparql.ini`:

```ini
[sparqlQueries]
YOUR_QUERY_NAME = SELECT ...
```

For detailed information about specific configurations, refer to the respective component documentation.

## Default Dataset and Data Conversion

By default, MetaboT is configured to automatically connect to the public ENPKG endpoint, which hosts an annotated mass spectrometry knowledge graph derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset allows you to explore and evaluate the capabilities of MetaboT immediately, without the need to convert your own data.

If you wish to use your own mass spectrometry data:
- Prepare your data by processing and annotating it using your preferred workflow.
- Convert your processing and annotation results into a knowledge graph format using the [Experimental Natural Products Knowledge Graph library](https://doi.org/10.1021/acscentsci.3c00800).
- Update the `KG_ENDPOINT_URL` in your `.env` file to point to your custom knowledge graph endpoint.