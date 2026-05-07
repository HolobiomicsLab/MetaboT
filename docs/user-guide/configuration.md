# Configuration

This guide covers the configuration files and environment variables that control MetaboT's models, workflow, endpoints, and tracing.

## Configuration Files

The main configuration files live in `app/config/`:

- `params.ini`: language model definitions
- `langgraph.json`: agent graph and model assignments
- `sparql.ini`: schema and SPARQL helper queries
- `logging.ini`: console and file logging

User-specific secrets and runtime values should go in `.env` at the repository root.

## Model Configuration

MetaboT reads language model definitions from `app/config/params.ini`.

### Current Built-In Model Sections

| Section | Purpose |
| --- | --- |
| `llm_o` | primary OpenAI model configuration |
| `llm_mini` | secondary OpenAI model used for the SPARQL improvement chain |
| `deepseek_deepseek-chat` | DeepSeek chat endpoint |
| `deepseek_deepseek-reasoner` | DeepSeek reasoner endpoint |
| `ovh_Meta-Llama-3_1-70B-Instruct` | OVH-hosted Llama endpoint |
| `llm_litellm_openai` | LiteLLM-backed OpenAI config |
| `llm_litellm_deepseek` | LiteLLM-backed DeepSeek config |
| `llm_litellm_claude` | LiteLLM-backed Anthropic config |
| `llm_litellm_gemini` | LiteLLM-backed Gemini config |
| `llm_litellm_mistral` | LiteLLM-backed Mistral config |

### Example

```ini
[llm_o]
id = gpt-4o
temperature = 0
max_retries = 3

[deepseek_deepseek-chat]
id = deepseek-chat
temperature = 0
max_retries = 3
base_url = https://api.deepseek.com
```

### Supported Parameters

- `id`: provider-specific model identifier
- `temperature`: sampling temperature
- `max_retries`: retry count for model calls
- `base_url` or `api_base`: custom endpoint for OpenAI-compatible APIs

## Provider-to-Environment Variable Mapping

MetaboT maps providers to environment variables in `app/core/main.py`.

| Provider | Environment variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| OVH | `OVHCLOUD_API_KEY` |
| Hugging Face | `HUGGINGFACE_API_KEY` |

### Example `.env`

```env
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
OVHCLOUD_API_KEY=
HUGGINGFACE_API_KEY=
```

You only need to define the keys for the providers you actually use.

## Assigning Models to Agents

Agent wiring is controlled by `app/config/langgraph.json`.

Current default assignments:

```json
{
  "agents": [
    {"name": "Entry_Agent", "path": "app.core.agents.entry.agent", "llm_choice": "llm_o"},
    {"name": "ENPKG_agent", "path": "app.core.agents.enpkg.agent", "llm_choice": "llm_o"},
    {"name": "Sparql_query_runner", "path": "app.core.agents.sparql.agent", "llm_choice": "llm_o"},
    {"name": "Interpreter_agent", "path": "app.core.agents.interpreter.agent", "llm_choice": "llm_o"},
    {"name": "supervisor", "path": "app.core.agents.supervisor.agent", "llm_choice": "llm_o"},
    {"name": "Validator", "path": "app.core.agents.validator.agent", "llm_choice": "llm_o"}
  ]
}
```

To switch a specific agent to another model, change its `llm_choice` value to the target section name from `params.ini`.

## Endpoint Configuration

MetaboT reads the SPARQL endpoint in this order:

1. `--endpoint` command-line argument
2. `KG_ENDPOINT_URL` in `.env`
3. the default ENPKG endpoint

Example:

```env
KG_ENDPOINT_URL=https://enpkg.commons-lab.org/graphdb/repositories/ENPKG
SPARQL_USERNAME=
SPARQL_PASSWORD=
```

Use `SPARQL_USERNAME` and `SPARQL_PASSWORD` only when your endpoint requires authentication.

## LangSmith and Tracing

Tracing is optional. MetaboT enables it automatically if either of these is present:

- `LANGCHAIN_API_KEY`
- `LANGSMITH_API_KEY`

Recommended configuration:

```env
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=MetaboT
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

If no tracing key is present, MetaboT disables tracing automatically.

For running the repository's LangSmith-based automated benchmark evaluation, see [docs/examples/langsmith-evaluation.md](../examples/langsmith-evaluation.md).

## SPARQL and Schema Configuration

`app/config/sparql.ini` contains helper queries used to inspect or work with the graph schema. These are especially important when MetaboT needs to construct schema-aware prompts from an endpoint rather than from assumptions.

This file includes:

- class discovery queries
- property discovery queries
- excluded URI settings

If you adapt MetaboT to another graph, review `sparql.ini` together with the prompt files used by the validator and SPARQL agents.

## Adapting MetaboT to a New Knowledge Graph

For a graph that differs significantly from ENPKG, the most important adjustments are:

1. update `KG_ENDPOINT_URL`
2. check whether the schema can be extracted cleanly
3. revise prompt instructions in:
   - `app/core/agents/validator/prompt.py`
   - `app/core/agents/sparql/prompt.py`
   - `app/core/agents/sparql/tool_sparql.py`
4. adapt or replace entity resolver tools if your graph uses different identifier systems

The more your graph diverges from ENPKG in naming conventions and ontology structure, the more prompt tuning will matter.

## Logging

Logging behavior is defined in `app/config/logging.ini`.

By default, MetaboT logs to:

- the console
- a rotating log file

Useful adjustments:

- raise log level to `DEBUG` during development
- keep `INFO` for routine usage
- inspect file handler settings if you want larger or longer-lived logs

## Best Practices

- Keep one strong default model for most agents before experimenting with per-agent specialization.
- Start on the public ENPKG endpoint before switching to a custom graph.
- Add only the environment variables you need for the providers you are using.
- Treat prompt updates and resolver updates as part of the same portability work when moving to a new graph.

## Related Pages

- [Installation](../getting-started/installation.md)
- [Quick Start](../getting-started/quickstart.md)
- [Overview](overview.md)
