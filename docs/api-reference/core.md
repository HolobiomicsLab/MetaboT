# Core API Reference

This document provides detailed information about the core components and functions of MetaboT.

## Main Module

The main module (`app.core.main`) provides the primary entry points and core functionality for MetaboT.

### Functions

#### `link_kg_database`

```python
def link_kg_database(endpoint_url: str) -> RdfGraph
```

Initializes or loads an RDF graph connection to the knowledge graph.

**Parameters:**
- `endpoint_url` (str): The URL of the SPARQL endpoint

**Returns:**
- `RdfGraph`: An initialized RDF graph object

**Example:**
```python
graph = link_kg_database("https://enpkg.commons-lab.org/graphdb/repositories/ENPKG")
```

#### `llm_creation`

```python
def llm_creation(api_key: Optional[str] = None) -> Dict[str, ChatOpenAI]
```

Creates and configures language model instances based on the configuration file.

**Parameters:**
- `api_key` (Optional[str]): OpenAI API key (optional, can be set via environment variable)

**Returns:**
- `Dict[str, ChatOpenAI]`: Dictionary of initialized language models

**Example:**
```python
models = llm_creation()
llm = models['llm']  # Get the default model
```

#### `langsmith_setup`

```python
def langsmith_setup() -> None
```

Configures LangSmith integration for workflow tracking and monitoring.

**Example:**
```python
langsmith_setup()  # Sets up LangSmith environment
```

## Graph Management

The graph management module provides tools for interacting with the RDF knowledge graph.

### RdfGraph Class

```python
class RdfGraph:
    def __init__(self, query_endpoint: str, standard: str = "rdf"):
        """
        Initialize an RDF graph connection.
        
        Args:
            query_endpoint (str): SPARQL endpoint URL
            standard (str): RDF standard to use (default: "rdf")
        """
```

**Key Methods:**
- `get_schema`: Retrieves the graph schema
- `execute_query`: Runs SPARQL queries against the graph
- `save`: Persists the graph state

## Workflow Management

The workflow module (`app.core.workflow.langraph_workflow`) manages the processing pipeline.

### Functions

#### `create_workflow`

```python
def create_workflow(agents: Dict, evaluation: bool = False) -> Any
```

Creates a new workflow instance with the specified agents.

**Parameters:**
- `agents` (Dict): Dictionary of agent instances
- `evaluation` (bool): Whether to run in evaluation mode

**Returns:**
- Workflow instance

#### `process_workflow`

```python
def process_workflow(workflow: Any, question: str) -> Any
```

Processes a query through the workflow.

**Parameters:**
- `workflow`: The workflow instance
- `question` (str): The query to process

**Returns:**
- Query results

## Agent Factory

The agent factory module (`app.core.agents.agents_factory`) manages agent creation and configuration.

### Functions

#### `create_all_agents`

```python
def create_all_agents(models: Dict[str, ChatOpenAI], graph: RdfGraph) -> Dict
```

Creates all required agents for the workflow.

**Parameters:**
- `models`: Dictionary of language models
- `graph`: RDF graph instance

**Returns:**
- Dictionary of initialized agents

## Utility Functions

The utils module (`app.core.utils`) provides common utility functions.

### Functions

#### `setup_logger`

```python
def setup_logger(name: str) -> logging.Logger
```

Configures a logger instance.

**Parameters:**
- `name` (str): Logger name

**Returns:**
- Configured logger instance

#### `load_config`

```python
def load_config(config_path: str) -> configparser.ConfigParser
```

Loads a configuration file.

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- Parsed configuration object

## Error Handling

MetaboT provides several error types for handling specific scenarios:

```python
class MetaboTError(Exception):
    """Base error for MetaboT operations."""
    pass

class GraphConnectionError(MetaboTError):
    """Raised when unable to connect to the knowledge graph."""
    pass

class QueryExecutionError(MetaboTError):
    """Raised when a query fails to execute."""
    pass
```

## Usage Examples

### Basic Query Processing

```python
from app.core.main import link_kg_database, llm_creation
from app.core.workflow.langraph_workflow import create_workflow, process_workflow
from app.core.agents.agents_factory import create_all_agents

# Initialize components
graph = link_kg_database("your_endpoint_url")
models = llm_creation()
agents = create_all_agents(models, graph)

# Create and run workflow
workflow = create_workflow(agents)
results = process_workflow(workflow, "Your query here")
```

### Custom Agent Integration

```python
from app.core.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, model, graph):
        super().__init__(model, graph)
        
    def process(self, input_data):
        # Custom processing logic
        pass

# Add to workflow
agents['custom'] = CustomAgent(models['llm'], graph)
workflow = create_workflow(agents)
```

For more detailed information about specific components, refer to the respective module documentation.