# Agents API Reference 🤖

This document details the agent system in 🧪 MetaboT 🍵, including the various specialized agents and their roles in processing metabolomics queries.

---
## Agent Factory 🔧

The agent factory ([`app.core.agents.agents_factory`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/agents_factory.py)) manages the creation and configuration of all agents in the system:

- **ENPK Agent**: Located at [`app/core/agents/enpkg/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/enpkg/agent.py)
- **Entry Agent**: Located at [`app/core/agents/entry/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/entry/agent.py)
- **Interpreter Agent**: Located at [`app/core/agents/interpreter/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/interpreter/agent.py)
- **Sparql Agent**: Located at [`app/core/agents/sparql/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/agent.py)
- **Validator Agent**: Located at [`app/core/agents/validator/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/validator/agent.py)
- **Supervisor Agent**: Located at [`app/core/agents/supervisor/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/supervisor/agent.py)

### Functions

#### `create_all_agents` 🛠️

```python
def create_all_agents(models: Dict[str, ChatOpenAI], graph: RdfGraph) -> Dict[str, Any]
```

Creates and initializes all required agents for the 🧪 MetaboT 🍵 workflow.

**Parameters:**

- `models`: Dictionary of language models for different purposes
- `graph`: RDF graph instance for knowledge graph interactions

**Returns:**

- Dictionary of initialized agents

---
## Entry Agent 🚪

The entry agent ([`app.core.agents.entry.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/entry/agent.py)) serves as the initial point of contact for processing user queries.

### Class: EntryAgent

```python
class EntryAgent:
    def __init__(self, model: ChatOpenAI, graph: RdfGraph):
        """
        Initialize the entry agent.
        
        Args:
            model: Language model for query processing
            graph: RDF graph for data access
        """
```

**Key Methods:**

- `process_query`: Initial query processing and routing
- `validate_input`: Input validation and sanitization
- `determine_path`: Determines processing path for queries

---
## ENPKG Agent 🧪

The ENPKG agent ([`app.core.agents.enpkg.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/enpkg/agent.py)) handles metabolomics-specific processing.

### Class: ENPKGAgent

```python
class ENPKGAgent:
    """
    Specialized agent for metabolomics data processing.
    Handles chemical structure analysis and metabolomics-specific queries.
    """
```

**Tools:**

- `tool_chemicals`: Chemical structure analysis
- `tool_smiles`: SMILES notation processing
- `tool_target`: Target analysis
- `tool_taxon`: Taxonomic processing

---
## SPARQL Agent 🔎

The SPARQL agent ([`app.core.agents.sparql.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/sparql/agent.py)) manages interactions with the knowledge graph.

### Class: SPARQLAgent

```python
class SPARQLAgent:
    """
    Handles SPARQL query generation and execution.
    Optimizes queries for the knowledge graph.
    """
```

**Key Components:**

- `tool_sparql`: SPARQL query execution
- `tool_merge_result`: Result merging and processing
- `tool_wikidata_query`: Wikidata integration

---
## Interpreter Agent 📢

The interpreter agent ([`app.core.agents.interpreter.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/interpreter/agent.py)) processes and formats query results.

### Class: InterpreterAgent

```python
class InterpreterAgent:
    """
    Processes and formats query results for human readability.
    Handles data visualization requests.
    """
```

**Features:**

- Natural language result formatting
- Data visualization support
- Result contextualization

---
## Validator Agent ✅

The validator agent ([`app.core.agents.validator.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/validator/agent.py)) ensures data quality and consistency.

### Class: ValidatorAgent

```python
class ValidatorAgent:
    """
    Validates query results and ensures data quality.
    Performs error checking and consistency validation.
    """
```

**Validation Types:**

- Data consistency checks
- Result validation
- Error detection

---
## Agent Communication 💬

Agents communicate through a structured message passing system:

```python
class AgentMessage:
    """
    Structured message format for inter-agent communication.
    """
    def __init__(self, content: Any, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
```

---
## Tool Integration 🔌

Each agent can integrate specialized tools:

### Base Tool Class

```python
class BaseTool:
    """
    Base class for agent-specific tools.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    def run(self, *args, **kwargs):
        raise NotImplementedError
```

### Example Tool Implementation

```python
class ChemicalStructureTool(BaseTool):
    """
    Tool for chemical structure analysis.
    """
    def __init__(self):
        super().__init__(
            name="chemical_structure",
            description="Analyzes chemical structures in metabolomics data"
        )
    
    def run(self, structure_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for chemical structure analysis
        pass
```

---
## Usage Examples 📘

### Basic Agent Usage

```python
from app.core.agents.agents_factory import create_all_agents
from app.core.graph_management.RdfGraphCustom import RdfGraph

# Initialize components
graph = RdfGraph(endpoint_url="your_endpoint")
models = {
    'llm': your_language_model,
    'llm_3_5': your_backup_model
}

# Create agents
agents = create_all_agents(models, graph)

# Use specific agent
entry_agent = agents['entry']
result = entry_agent.process_query("Your query here")
```

### Custom Agent Integration

```python
class CustomAgent:
    def __init__(self, model, graph):
        self.model = model
        self.graph = graph
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self):
        return {
            'custom_tool': CustomTool()
        }
    
    def process(self, input_data):
        # Custom processing logic
        pass

# Add to agent factory
agents['custom'] = CustomAgent(models['llm'], graph)
```

### Tool Development

```python
class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Custom processing tool"
        )
    
    def run(self, input_data):
        # Tool implementation
        return processed_data
```

For more detailed information about specific agents or tools, refer to their respective module documentation.