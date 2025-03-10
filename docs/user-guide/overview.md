# 🧪 MetaboT 🍵 Overview ✨

🧪 MetaboT 🍵 is an advanced metabolomics analysis tool that combines AI-powered agents, graph-based data management, and sophisticated query capabilities to analyze and interpret metabolomics data.

## System Architecture 🏗️

### Core Components ⚙️

```mermaid
graph TB
    A[User Query] --> B[Entry Agent]
    B --> G[Validator Agent]
    G --> C[Supervisor Agent]
    C <--> D[ENPKG Agent]
    C <--> E[SPARQL Agent]
    C <--> F[Interpreter Agent]
     E  --> H[Knowledge Graph]
    
   
```

- **Entry Agent** 🚪
    - Accepts user queries and input files (if provided) and performs initial processing.

- **Validator Agent** ✅
    - Validates user questions for knowledge graph.
    - Verifies plant names using the database.
    - Checks question content against the knowledge graph schema.

- **Supervisor Agent** 🎛️
    - Orchestrates the workflow between agents.
    - Manages state and context throughout query processing.
    - Ensures proper sequencing of operations.

- **ENPKG Agent** 🧪
    - Handles metabolomics-specific processing.
    - Provides resolutions to the entities mentioned in the question.
  

- **SPARQL Agent** 🔎
    - Generates and executes queries against the RDF knowledge graph.
    - Optimizes query performance.
    - Handles complex graph traversals.

- **Interpreter Agent** 📢
    - Processes and formats query results.
    - Generates human-readable outputs.
    - Handles data visualization requests.


### Knowledge Graph Integration 🔗

🧪 MetaboT 🍵 utilizes a sophisticated RDF-based knowledge graph that:

- Stores metabolomics data and relationships.
- Enables complex query capabilities.
- Supports data integration from multiple sources.
- Maintains data provenance.

**Note:**  By default, 🧪 MetaboT 🍵 connects to the public ENPKG endpoint which hosts an open, annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset enables you to explore all features of 🧪 MetaboT 🍵 without the need for custom data conversion immediately. To use 🧪 MetaboT 🍵 on your mass spectrometry data, the processed and annotated results must first be converted into a knowledge graph format using the ENPKG tool. For more details on converting your own data, please refer to the [*Experimental Natural Products Knowledge Graph library*](https://github.com/enpkg) and the [associated publication](https://doi.org/10.1021/acscentsci.3c00800).

## Key Features 🚀

### Query Processing 🔍

🧪 MetaboT 🍵 supports various types of queries:

- **Standard Queries**: Pre-defined queries for common analyses.
- **Custom Queries**: User-defined natural language queries.
- **Knowledge Graph Integration**: Access and analyze data from a comprehensive knowledge graph.
- **Advanced Data Processing**: Perform complex data analysis tasks with ease.
- **Visualization Tools**: Generate visualizations to better understand your data.

For development updates, please refer to the [`dev`](https://github.com/holobiomicslab/MetaboT/tree/dev) branch.
 

### AI-Powered Processing 🤖

🧪 MetaboT 🍵 leverages advanced AI capabilities through:

- **Language Models**
    - Natural language query processing
    - Context-aware responses
    - Result interpretation

- **Agent Collaboration**
    - Multi-agent workflow coordination
    - Specialized task processing
    - Adaptive response generation

## Workflow Examples 🛠️

### Basic Feature Analysis 📝

```mermaid
sequenceDiagram
    participant User
    participant Entry
    participant Validator
    participant Supervisor
    participant ENPKG
    participant SPARQL 
    participant Graph
    participant Interpreter
   
    User->>Entry: Submit feature query
    Entry->>Validator: Preprocess the query
    Validator->>Supervisor: Validate the question
    Supervisor->>ENPKG:Select the next agent 
    Supervisor->>SPARQL: Provide the question and resolved entities
    Supervisor->>Interpreter: Provide the results
    SPARQL->>Graph: Generate and execute SPARQL query 
    ENPKG-->>Supervisor: Provide resolved entities
    SPARQL-->>Supervisor: Provide the results
    Interpreter-->>Supervisor: Provide the interpreted results
    Supervisor-->>User: Present final results
```


## Performances  ⚡️

### Query Optimization 🔧

- Use highly targeted, knowledge-graph-centric queries that are clearly formatted
- Leverage standard queries for common operations
- Consider query complexity and data volume

## Best Practices 👍

1. **Query Design**
    - Start with standard queries when possible
    - Build custom queries incrementally
    - Test queries with smaller datasets first


2. **System Configuration**
    - Keep environment variables updated
    - Monitor system resources
    - Regular maintenance of graph database

## Integration Capabilities 🔌

🧪 MetaboT 🍵 can be integrated with:

- External databases
- Custom analysis pipelines
- Visualization tools
- Reporting systems

## Future Developments 🔮

Planned enhancements include:

- Enhanced visualization capabilities
- Additional analysis algorithms
- Expanded database integrations
- Improved performance optimization

For detailed information about specific components, please refer to the respective sections in the documentation.