# Core API Reference ⚙️

This document provides detailed information about the core components and functions of 🧪 MetaboT 🍵.

---
## Main Module 🚀

The main module ([`app.core.main`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/main.py)) provides the primary entry points and core functionality for 🧪 MetaboT 🍵.

### Functions

#### `link_kg_database` 🔗

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

#### `llm_creation` 🤖

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

#### `langsmith_setup` 🛠️

```python
def langsmith_setup() -> None
```

Configures LangSmith integration for workflow tracking and monitoring. If the environment variable LANGCHAIN_API_KEY (or LANGSMITH_API_KEY) is provided, the function enables tracing and configures the default project and endpoint. Otherwise, it disables tracing.

For advanced configuration details, see [Advanced Configuration](docs/getting-started/quickstart#advanced-configuration).

**Example:**
```python
langsmith_setup()  # Configures LangSmith integration if API key is provided
```

---
## Graph Management 📡

The graph management module ([`app.core.graph_management.RdfGraphCustom`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/graph_management/RdfGraphCustom.py)) provides tools for interacting with the RDF knowledge graph.

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

---
## Workflow Management 🔄

The workflow module ([`app.core.workflow.langraph_workflow`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/workflow/langraph_workflow.py)) manages the processing pipeline.

### Functions

#### `create_workflow` 🏗️

```python
def create_workflow(agents: Dict, evaluation: bool = False) -> Any
```

Creates a new workflow instance with the specified agents.

**Parameters:**
- `agents` (Dict): Dictionary of agent instances
- `evaluation` (bool): Whether to run in evaluation mode

**Returns:**
- Workflow instance

#### `process_workflow` 🔄

```python
def process_workflow(workflow: Any, question: str) -> Any
```

Processes a query through the workflow.

**Parameters:**
- `workflow`: The workflow instance
- `question` (str): The query to process

**Returns:**
- Query results

---
## Agent Factory 🏭

The agent factory module ([`app.core.agents.agents_factory`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/agents_factory.py)) manages agent creation and configuration.

### Functions

#### `create_all_agents` 🛠️

```python
def create_all_agents(models: Dict[str, ChatOpenAI], graph: RdfGraph) -> Dict
```

Creates all required agents for the workflow.

**Parameters:**
- `models`: Dictionary of language models
- `graph`: RDF graph instance

**Returns:**
- Dictionary of initialized agents

---
## Utility Functions 🧰

The utils module ([`app.core.utils`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/utils.py)) provides common utility functions.

### Functions

#### `setup_logger` 📝

```python
def setup_logger(name: str) -> logging.Logger
```

Configures a logger instance.

**Parameters:**
- `name` (str): Logger name

**Returns:**
- Configured logger instance

#### `load_config` 📂

```python
def load_config(config_path: str) -> configparser.ConfigParser
```

Loads a configuration file.

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- Parsed configuration object

---
## Database Management 💾

The database management module provides two specialized databases for managing tools data and workflow state.

### Tools Database 🔧

The tools database ([`app.core.memory.tools_database`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/memory/tools_database.py)) manages data associated with agent tools.

```python
def tools_database() -> ToolsDatabaseManager
```

Creates or returns a singleton instance of the tools database manager.

**Features:**

- Automatically discovers and tracks tool usage
- Maintains interaction history
- Stores tool-specific data
- Supports both SQLite (default) and custom database backends

**Configuration:**

- Default: Creates local `tools_database.db` file
- Custom: Set via environment variables:
  - `DATABASE_URL`: Database connection string
  - `TOOLS_DATABASE_MANAGER_CLASS`: Custom manager class path

### Memory Database 💭

The memory database ([`app.core.memory.custom_sqlite_file`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/memory/custom_sqlite_file.py)) manages workflow state and checkpoints.

```python
def memory_database() -> SqliteCheckpointerSaver
```

Creates or returns a singleton instance of the memory database manager.

**Features:**

- Saves workflow state checkpoints
- Supports multi-threading (essential for Streamlit)
- Automatic cleanup on restart
- Thread-safe operations

**Configuration:**

- Default: Creates local `langgraph_checkpoint.db` file
- Custom: Set via environment variables:
  - `DATABASE_URL`: Database connection string
  - `MEMORY_DATABASE_MANAGER_CLASS`: Custom manager class path

**Example:**
```python
from app.core.memory.database_manager import memory_database, tools_database

# Initialize databases
tools_db = tools_database()  # Returns SqliteToolsDatabaseManager by default
memory_db = memory_database()  # Returns SqliteCheckpointerSaver by default

# Create workflow with memory
workflow = create_workflow(agents, evaluation=False)
app = workflow.compile(checkpointer=memory_db)
```


---
## Usage Examples 📘

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
workflow = create_workflow(agents,evaluation = False)
results = process_workflow(workflow, "Your query here")
```
