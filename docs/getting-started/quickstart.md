# Quick Start

This page gets you from installation to a first successful MetaboT query as quickly as possible.

## Try the Public Demo First

If you want to see the system before installing anything, use the public demonstrator:

[https://metabot.holobiomicslab.eu](https://metabot.holobiomicslab.eu)

The demo is connected to the ENPKG knowledge graph built from an open dataset of [1,600 plant extracts](https://doi.org/10.1093/gigascience/giac124).

## Minimal Local Setup

After following the [Installation Guide](installation.md), a minimal `.env` file can be as small as:

```env
OPENAI_API_KEY=your_api_key_here
```

If you do not set `KG_ENDPOINT_URL`, MetaboT uses the public ENPKG endpoint by default.

## Run a Standard Question

MetaboT ships with predefined examples listed in `app/data/standard_questions.txt`.

Run the first one:

```bash
python -m app.core.main -q 1
```

This command:

- loads the configured models
- connects to the default or configured SPARQL endpoint
- runs one of the bundled benchmark-style questions
- prints the result and, when relevant, the generated SPARQL and CSV path

## Run a Custom Question

```bash
python -m app.core.main -c "What are the SIRIUS structural annotations for Tabernaemontana coffeoides?"
```

Another example from the manuscript:

```bash
python -m app.core.main -c "Which lab extracts have bioassay results with inhibition percentages above 50% against Leishmania donovani?"
```

## Typical Question Types

MetaboT is most useful for questions such as:

- taxon-centric annotation queries
- chemical class filtering
- cross-sample comparisons
- bioassay and target queries
- structure- or spectrum-linked lookups

Examples:

```bash
python -m app.core.main -c "Count the number of LCMS features in negative ionization mode"
python -m app.core.main -c "List the bioassay results at 10ug/mL against T.cruzi for lab extracts of Tabernaemontana coffeoides"
python -m app.core.main -c "Which extracts have features annotated as aspidosperma-type alkaloids by CANOPUS with a probability score above 0.5?"
```

## Override the Endpoint

To query another knowledge graph endpoint for a single run:

```bash
python -m app.core.main -c "Which extracts contain flavonoids?" --endpoint https://your-endpoint.example/sparql
```

For a persistent change, set `KG_ENDPOINT_URL` in `.env`.

## Run the Streamlit App

The repository also contains a Streamlit interface:

```bash
export ADMIN_OPENAI_KEY=your_api_key_here
export PYTHONPATH="$(pwd):${PYTHONPATH}"
streamlit run streamlit_webapp/streamlit_app.py
```

This interface is useful when you want a chat-style workflow, file uploads, or interactive result exploration.

## What Happens Internally?

For a typical knowledge question, the workflow is:

1. `Entry Agent` classifies the request.
2. `Validator Agent` checks whether the question is valid for the graph.
3. `Supervisor Agent` decides whether entity resolution is needed.
4. `ENPKG_agent` resolves taxa, targets, or chemical entities when necessary.
5. `Sparql_query_runner` generates and executes schema-aware SPARQL.
6. `Interpreter_agent` summarizes or visualizes the output if needed.

## Result Files

Large results may be written to temporary CSV files. This is expected behavior and helps MetaboT avoid overflowing the LLM context window while still returning the complete result set.

## Troubleshooting

### The query fails immediately

- Confirm that your environment is activated.
- Make sure at least one required API key is set.
- Test with the default ENPKG endpoint before debugging a custom endpoint.

### The endpoint works but the question is rejected

MetaboT validates questions against the knowledge graph schema. Try a simpler question first, then increase specificity.

### Import errors when running Streamlit

Run Streamlit from the repository root and set:

```bash
export PYTHONPATH="$(pwd):${PYTHONPATH}"
```

## Next Steps

- Read the [Overview](../user-guide/overview.md) for the architecture
- Update providers and endpoints in the [Configuration Guide](../user-guide/configuration.md)
- Browse additional [examples](../examples/basic-usage.md)
