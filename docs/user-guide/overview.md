# 🧪 MetaboT 🍵 Overview ✨

🧪 MetaboT 🍵 is an advanced metabolomics analysis tool that combines AI-powered agents, graph-based data management, and sophisticated query capabilities to analyze and interpret metabolomics data.

## System Architecture 🏗️

### Core Components ⚙️

```mermaid
graph TB
    A[User Query] --> B[Entry Agent]
    B --> C[Supervisor Agent]
    C --> D[ENPKG Agent]
    C --> E[SPARQL Agent]
    C --> F[Interpreter Agent]
    C --> G[Validator Agent]
    D & E & F & G --> H[Knowledge Graph]
    H --> I[Results]
```

- **Entry Agent** 🚪
    - Processes initial user queries.
    - Performs query validation and preprocessing.
    - Routes queries to appropriate processing paths.

- **Supervisor Agent** 🎛️
    - Orchestrates the workflow between agents.
    - Manages state and context throughout query processing.
    - Ensures proper sequencing of operations.

- **ENPKG Agent** 🧪
    - Handles metabolomics-specific processing.
    - Manages chemical structure analysis.
    - Processes bioassay data.

- **SPARQL Agent** 🔎
    - Executes queries against the RDF knowledge graph
    - Optimizes query performance
    - Handles complex graph traversals

- **Interpreter Agent** 📢
    - Processes and formats query results
    - Generates human-readable outputs
    - Handles data visualization requests

- **Validator Agent** ✅
    - Ensures data quality and consistency
    - Validates query results
    - Performs error checking

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

- **Standard Queries**: Pre-defined queries for common analyses
- **Custom Queries**: User-defined natural language queries.
- **Knowledge Graph Integration**: Access and analyze data from a comprehensive knowledge graph.
- **Advanced Data Processing**: Perform complex data analysis tasks with ease.
- **Visualization Tools**: Generate visualizations to better understand your data.

For development updates, please refer to the [`dev`](https://github.com/holobiomicslab/MetaboT/tree/dev) branch.
 
### Data Analysis Capabilities 📊

- **Chemical Structure Analysis** 🧬
    - SIRIUS annotation
    - ISDB annotation support
    - Structure similarity comparisons

- **Metabolomics Analysis** 🧪
    - Feature detection and analysis
    - Ionization mode processing
    - Retention time analysis

- **Bioassay Integration** 💊
    - Activity data analysis
    - Inhibition studies
    - Concentration-response relationships

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
    participant ENPKG
    participant SPARQL
    participant Graph

    User->>Entry: Submit feature query
    Entry->>ENPKG: Process feature request
    ENPKG->>SPARQL: Generate SPARQL query
    SPARQL->>Graph: Execute query
    Graph-->>SPARQL: Return results
    SPARQL-->>ENPKG: Process results
    ENPKG-->>Entry: Format output
    Entry-->>User: Present results
```

### Chemical Structure Analysis 🧪

```mermaid
sequenceDiagram
    participant User
    participant Entry
    participant SPARQL
    participant Validator
    participant Graph

    User->>Entry: Submit structure query
    Entry->>SPARQL: Generate query
    SPARQL->>Graph: Execute query
    Graph-->>SPARQL: Return structures
    SPARQL->>Validator: Validate results
    Validator-->>Entry: Confirm validity
    Entry-->>User: Present structures
```

## Performances  ⚡️

### Query Optimization 🔧

- Use specific queries when possible
- Leverage standard queries for common operations
- Consider query complexity and data volume

### Resource Management 🗄️

- Monitor memory usage during large queries
- Consider batch processing for extensive analyses
- Utilize caching when appropriate

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