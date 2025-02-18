# Agents API Reference 🤖

This document details the agent system in 🧪 MetaboT 🍵, including the various specialized agents and their roles in processing metabolomics queries.

---

## Agent Factory 🔧

The agent factory ([`app.core.agents.agents_factory`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/agents_factory.py)) manages the creation and configuration of all agents in the system:

- **ENPK Agent**: Located at [`app/core/agents/enpkg/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/enpkg/agent.py)
- **Entry Agent**: Located at [`app/core/agents/entry/agent.py`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/entry/agent.py)
- **Interpreter Agent**: Located at [`app/core/agents/interpreter/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/interpreter/agent.py)
- **Sparql Agent**: Located at [`app/core/agents/sparql/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/agent.py)
- **Validator Agent**: Located at [`app/core/agents/validator/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/validator/agent.py)
- **Supervisor Agent**: Located at [`app/core/agents/supervisor/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/supervisor/agent.py)

---

## Common Mechanism for Tool Import

All agents are created via their respective factory functions. These functions use the common utility `import_tools` to dynamically scan the agent’s directory for Python files with names beginning with the prefix `tool_`. Each such file contains an implementation extending the base class `BaseTool`. The imported tools provide specialized functions such as:

- **File Analysis:** For instance, a tool that analyzes submitted files, returning the full file path and a summary of contents.
- **Chemical Structure Analysis:** Analyzing molecular structures.
- **SMILES Processing:** Handling SMILES string representations.
- **Molecular Target Analysis and Taxonomic Processing:** Providing detailed analyses for metabolomics data.

---

## Entry Agent 🚪

The Entry Agent is instantiated via the factory function [`create_agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/entry/agent.py) in the entry agent module.

**Purpose:**  
- Acts as the initial point of contact for processing user queries.
- Preprocesses queries, including detecting and analyzing submitted files.

**Key Features:**  
- Dynamically loads tools from its directory (e.g., `FILE_ANALYZER`) to analyze files.
- Uses a customized prompt from [prompt.py](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/entry/prompt.py) to classify and route queries.
- Returns an `AgentExecutor` that encapsulates both the agent and its integrated tools for efficient query processing.

---

## ENPKG Agent 🧪

The ENPKG Agent is instantiated via the factory function [`create_agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/enpkg/agent.py) in the ENPKG agent module.

**Purpose:**  
- Specializes in processing metabolomics data related to natural products, with a focus on chemical structure analysis.

**Key Features:**  
- Dynamically imports specialized tools using `import_tools` with an additional configuration parameter `openai_key`.
- Utilizes a dedicated prompt from [prompt.py](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/enpkg/prompt.py) tailored for metabolomics queries.
- Integrated tools include:
  - **tool_chemicals:** Analyzes chemical structures.
  - **tool_smiles:** Processes SMILES representations.
  - **tool_target:** Performs molecular target analysis.
  - **tool_taxon:** Conducts taxonomic processing of metabolomics data.

---

## SPARQL Agent 🔎

The SPARQL Agent ([`app.core.agents.sparql.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/sparql/agent.py)) manages interactions with the knowledge graph.

### Class: SPARQLAgent

```python
class SPARQLAgent:
    """
    Handles SPARQL query generation and execution.
    Optimizes queries for the knowledge graph.
    """
```

**Key Components:**
- `tool_sparql`: SPARQL query execution.
- `tool_merge_result`: Merges and processes query results.
- `tool_wikidata_query`: Integrates with Wikidata for query enrichment.

---

## Interpreter Agent 📢

The Interpreter Agent ([`app.core.agents.interpreter.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/interpreter/agent.py)) processes and formats query results for human readability.

### Class: InterpreterAgent

```python
class InterpreterAgent:
    """
    Processes and formats query results for human readability.
    Supports data visualization and context enrichment.
    """
```

**Features:**
- Natural language result formatting.
- Data visualization support.
- Context enrichment of results.

---

## Validator Agent ✅

The Validator Agent ([`app.core.agents.validator.agent`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/validator/agent.py)) ensures data quality and consistency.

### Class: ValidatorAgent

```python
class ValidatorAgent:
    """
    Validates query results and ensures data quality.
    Performs error checking and consistency validation.
    """
```

**Validation Types:**
- Data consistency checks.
- Result validation.
- Error detection.

---

## Agent Communication 💬

Agents communicate using a structured message passing system:

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

Each agent can integrate specialized tools.

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

# Use a specific agent
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