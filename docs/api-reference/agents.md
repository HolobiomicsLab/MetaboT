# Agents API Reference 🤖

This document details the agent system in the application, including the specialized agents and their roles in processing queries.

## Common Architecture

All agents in the system share a similar architectural pattern and are managed by the agent factory ([`app.core.agents.agents_factory`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/agents_factory.py)):

**Core Components:**

- **Dynamic Agent Creation**: Loads agent modules based on configuration settings
- **Flexible Parameter Handling**: Uses introspection to pass only required parameters to each agent
- **LLM Selection**: Supports configuration-based and agent-specific LLM selection
- **Session Management**: Maintains consistent session IDs across the agent ecosystem
- **Error Handling**: Provides robust logging and exception handling

### Core Factory Function

The `create_all_agents` function serves as the entry point for initializing the entire agent ecosystem:

```python
def create_all_agents(llms, graph, openai_key=None, session_id=None):
    """
    Dynamically create and initialize all agent modules as specified in the configuration.
    
    Parameters:
        llms (dict): A dictionary mapping LLM keys to their instances.
        graph: The graph instance used by the agents.
        openai_key (str, optional): The OpenAI API key to be used by agents.
        session_id (str, optional): A unique session identifier.
        
    Returns:
        dict: A dictionary mapping agent names to their created executor instances.
    """
```
## Individual Agent Architecture

Each agent in the system follows a consistent structural pattern while maintaining specialized functionality.

### Common Agent Components

- **Creation Function**: Each agent implements a `create_agent` function that returns an `AgentExecutor`
- **Tool Management**: Dynamically loads tools from its directory using the `import_tools` utility
- **Role-Specific Prompts**: Defines behavior through customized prompts
- **LLM Integration**: Utilizes language models as reasoning engines
- **Logging**: Implements consistent logging for monitoring and debugging

### Standard Agent Structure

```python
def create_agent(llms, graph, openai_key, llm_instance=None) -> AgentExecutor:
    """
    Creates and configures an agent with its specialized tools.
    
    Parameters:
        llms (dict): Available language models.
        graph: The knowledge graph instance.
        openai_key (str): API key for OpenAI services.
        llm_instance: Optional specific LLM instance to use.
        
    Returns:
        AgentExecutor: A configured agent executor instance.
    """
    # Load tools dynamically from the agent's directory
    # Configure the agent with appropriate prompts
    # Return an AgentExecutor instance
```
    
**Agent Locations:**

- **ENPKG Agent**: [`app/core/agents/enpkg/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/enpkg/agent.py)
- **Entry Agent**: [`app/core/agents/entry/agent.py`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/core/agents/entry/agent.py)
- **Interpreter Agent**: [`app/core/agents/interpreter/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/interpreter/agent.py)
- **SPARQL Agent**: [`app/core/agents/sparql/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/agent.py)
- **Validator Agent**: [`app/core/agents/validator/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/validator/agent.py)
- **Supervisor Agent**: [`app/core/agents/supervisor/agent.py`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/supervisor/agent.py)

---

## Entry Agent 🚪

The Entry Agent serves as the first point of contact for user interactions.

**Purpose:**

- Initial query processing and classification
- File analysis for submitted documents


**Key Features:**

- Classifies queries into "New Knowledge Question" or "Help me understand Question"
- Analyzes submitted files using the FILE_ANALYZER tool
- Validates query completeness and requests clarification when needed

**Tools:**

- FILE_ANALYZER: Processes and analyzes submitted files, providing file paths and content summaries

**Usage Cases:**

- When users submit new queries requiring database information
- When files need to be analyzed
- For follow-up questions requiring context from previous conversations

---

## Validator Agent ✅

The Validator Agent ensures query validity and data quality.

**Purpose:**

- Validates user queries against database capabilities
- Ensures data quality and consistency
- Provides feedback for invalid queries

**Validation Checks:**

- Plant name verification in database
- Query compatibility with schema
- Content relevance to available nodes/entities

**Tools:**

- PLANT_DATABASE_CHECKER: Verifies plant names in database

**Validation Criteria:**

- Plant-specific and feature-related queries
- Grouping, counting, and annotation comparisons
- Schema compatibility
- Data availability

---

## Supervisor Agent 👨‍💼

The Supervisor Agent orchestrates the interaction between all other agents in the system.

**Purpose:**

- Coordinates information flow between agents
- Makes routing decisions based on query content
- Ensures proper processing sequence
- Manages agent responses and task completion

**Decision Making:**

- Routes queries containing entities (compounds, taxa, targets) to ENPKG Agent
- Forwards resolved entities and queries to SPARQL Agent
- Directs query results to Interpreter Agent when needed
- Determines when to complete the process



---

## ENPKG Agent 🧬

The ENPKG Agent specializes in resolving and standardizing entities mentioned in queries.

**Purpose:**

- Resolves entity references to standardized identifiers
- Handles multiple types of entities (chemicals, taxa, targets)
- Provides unit information for numerical values

**Tools:**

- CHEMICAL_RESOLVER: Maps chemical names to NPC Class URIs
- TAXON_RESOLVER: Resolves taxonomic names to Wikidata IRIs
- TARGET_RESOLVER: Maps target names to ChEMBLTarget IRIs
- SMILE_CONVERTER: Converts SMILE structures to InChIKey notation

**Entity Types Handled:**

- Natural product compounds (with chemical class identifiers)
- Taxonomic names (with Wikidata IRIs)
- Molecular targets (with ChEMBL IRIs)
- Chemical structures (in SMILE notation)

---

## SPARQL Agent 🔎

The SPARQL Agent handles the generation and execution of database queries.

**Purpose:**

- Generates and executes SPARQL queries
- Handles query optimization and improvement
- Manages data retrieval and formatting

**Key Components:**

- Query Generation Chain: Creates initial SPARQL queries
- Query Improvement Chain: Refines queries if initial results are empty
- Vector Search: Finds similar successful queries for improvement
- Schema Validation: Ensures queries follow database schema

**Tools:**

- SPARQL_QUERY_RUNNER: Executes SPARQL queries against the knowledge graph
- WIKIDATA_QUERY_TOOL: Retrieves data from Wikidata in specific case
- OUTPUT_MERGE: Combines results from multiple sources

**Query Processing Features:**

- Automatic query improvement when no results are found
- Token management for large result sets
- Results are automatically saved as temporary CSV files in the user's session directory
- Local CSV storage enables users to perform additional analysis or processing on the results

---

## Interpreter Agent 📊

The Interpreter Agent processes and formats query results for human understanding.

**Purpose:**

- Processes SPARQL query outputs
- Handles file interpretation
- Generates visualizations
- Provides clear, formatted answers


**Input Processing:**
- Handles SPARQL query results
- Processes user-submitted files
- Interprets data files

**Tools:**

- INTERPRETER_TOOL: Main tool for data interpretation and visualization
- SPECTRUM_PLOTTER: Provides the url with a plot of a spectrum given its USI

**Output Types:**

- Text interpretations of query results
- Generated visualizations
- Formatted data summaries
- File path references for downloads
- URL which connects to the Metabolomics Spectrum Resolver tool

---

## Agent Interaction Architecture 🔄

The agent system is implemented using [LangGraph](https://www.langchain.com/langgraph)'s StateGraph, where agents operate as nodes in a directed graph with state-managed transitions.

**Core Architecture:**
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]  # Accumulated messages
    next: str  # Next routing target
```

**Workflow Components:**

1. Graph Structure:
    - Entry_Agent as the designated entry point
    - Nodes representing individual agents
    - Conditional edges defining valid transitions
    - State preservation across transitions

2. Routing Logic:
    - Entry_Agent can route to Supervisor or Validator
    - Validator makes routing decisions based on query validation
    - Supervisor dynamically routes to specialized agents
    - Process ends when valid response generated or error detected

3. State Management:
      - Messages accumulate throughout processing
      - Each agent adds its output to message history
      - State maintained across all transitions
      - Metadata preserved for context

**Communication Patterns:**

1. Primary Flow:
   ```
   Entry_Agent → Validator → Supervisor → [Specialized Agents] → __end__
   ```

2. Conditional Branching:
    * Validator routes based on query validity
    * Supervisor routes based on query content analysis
    * Dynamic routing to specialized agents as needed

3. Message Handling:
    * Human messages initiate workflow
    * Agent responses added to message sequence
    * State updates trigger next agent selection
    * Final response terminates workflow

**This architecture ensures:**

  * Clear communication paths
  * Stateful processing
  * Dynamic routing
  * Error handling
  * Process monitoring

---

## Agent Setup Guidelines 🧑‍💻

### Agent Directory Creation
Create a dedicated folder for your agent within the [`app/core/agents/`](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents) directory.

### Standard File Structure
- **Agent (`agent.py`)**: Copy from an existing agent unless your tool requires private class property access. Refer to "If Your Tool Serves as an Agent" for special cases.
  > Psst... don't let the complexities of Python imports overcomplicate your flow—trust the process!

- **Prompt (`prompt.py`)**: Adapt the prompt for your specific context/tasks.

- **Tools (`tool_xxxx.py`)** (optional): Inherit from the LangChain `BaseTool`, defining:
    - `name`, `description`, `args_schema`
    - A Pydantic model for input validation
    - The `_run` method for execution

### Supervisor Configuration
Modify the supervisor prompt (see [supervisor prompt](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/supervisor/prompt.py)) to detect and select your agent. Our AI PR-Agent 🤖 is triggered automatically through issues and pull requests, so you'll be in good hands!

### Configuration Updates
Update [`app/config/langgraph.json`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/config/langgraph.json) to include your agent in the workflow and specify `llm_choice` based on the models defined in [`app/config/params.ini`](https://github.com/HolobiomicsLab/MetaboT/blob/main/app/config/params.ini). Available models include:

- OpenAI models: `llm_preview`, `llm_o`, `llm_mini`
- OVH models: `ovh_Meta-Llama-3_1-70B-Instruct`
- Deepseek models: `deepseek_deepseek-chat`, `deepseek_deepseek-reasoner`
- LiteLLM compatible models: `llm_litellm_openai`, `llm_litellm_deepseek`, `llm_litellm_claude`, `llm_litellm_gemini`

Choose the appropriate model based on your agent's requirements for reasoning capabilities and performance. For reference, see [langgraph.json](https://github.com/holobiomicslab/MetaboT/tree/main/app/config/langgraph.json). If you need to add a new language model, refer to the [Language Model Configuration](../getting-started/installation.md#language-model-configuration) guide.

### If Your Tool Serves as an Agent
For LLM-interaction, make sure additional class properties are set in `agent.py` (refer to [tool_sparql.py](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/tool_sparql.py) and [agent.py](https://github.com/holobiomicslab/MetaboT/blob/main/app/core/agents/sparql/agent.py)). Keep it snazzy and smart!
