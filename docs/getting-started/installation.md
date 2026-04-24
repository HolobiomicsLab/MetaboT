# Installation

This guide installs the current repository version of MetaboT for local development or research use.

## Prerequisites

You will need:

- Python 3.11
- `conda` or `miniconda` recommended
- `git`
- An API key for at least one supported LLM provider

Optional but useful:

- `docker` and `docker-compose` for containerized runs
- A LangSmith key for tracing and evaluation logs
- WSL if you want to run MetaboT on Windows

## Clone the Repository

```bash
git clone https://github.com/HolobiomicsLab/MetaboT.git
cd MetaboT
```

The default branch is `main`.

## Create the Environment

### Recommended: Conda

```bash
conda env create -f environment.yml
conda activate metabot
```

### Alternative: Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Linux Notes

On Debian or Ubuntu, install compiler headers first if needed:

```bash
sudo apt-get update
sudo apt-get install -y python3-dev build-essential
```

### Windows Notes

MetaboT is best run through WSL on Windows:

```bash
wsl --install
```

Inside WSL, follow the Linux installation steps above.

## Configure Environment Variables

Create a `.env` file in the project root.

### Minimal Setup for the Default ENPKG Endpoint

```env
OPENAI_API_KEY=your_api_key_here
```

If `KG_ENDPOINT_URL` is not set, MetaboT defaults to:

```text
https://enpkg.commons-lab.org/graphdb/repositories/ENPKG
```

### Full Example

```env
# LLM providers
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
OVHCLOUD_API_KEY=
HUGGINGFACE_API_KEY=

# Optional custom endpoint
KG_ENDPOINT_URL=https://enpkg.commons-lab.org/graphdb/repositories/ENPKG
SPARQL_USERNAME=
SPARQL_PASSWORD=

# Optional tracing
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=MetaboT
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

MetaboT reads provider-specific keys based on the model configuration in `app/config/params.ini`.

## Verify the Installation

The fastest smoke test is to run one of the bundled standard questions:

```bash
python -m app.core.main -q 1
```

You can also run the installation test script:

```bash
python app/tests/installation_test.py
```

Successful execution confirms that MetaboT can initialize the workflow, connect to the knowledge graph, and execute a query.

## Optional: Run with Docker

```bash
docker-compose build
docker-compose run --rm metabot python -m app.core.main -q 1
```

## Endpoint Configuration

To use a custom SPARQL endpoint, either:

- set `KG_ENDPOINT_URL` in `.env`, or
- pass `--endpoint` at runtime

Example:

```bash
python -m app.core.main -c "Which extracts contain flavonoids?" --endpoint https://your-endpoint.example/sparql
```

If the endpoint requires authentication, add:

```env
SPARQL_USERNAME=your_username
SPARQL_PASSWORD=your_password
```

## Using a Different LLM Provider

MetaboT currently ships example model configurations for:

- OpenAI
- DeepSeek
- Anthropic via LiteLLM
- Gemini via LiteLLM
- Mistral via LiteLLM
- OVH-hosted Llama

To switch providers, update the relevant section in `app/config/params.ini` and ensure the matching API key is present in `.env`.

## Common Issues

### SPARQL Endpoint Errors

- Check that `KG_ENDPOINT_URL` points to a live endpoint.
- Confirm credentials if your endpoint requires authentication.
- Test against the default ENPKG endpoint first to isolate endpoint-specific issues.

### Module Import Errors

If Python cannot find the `app` package during ad hoc runs, make sure you are executing commands from the repository root and that your environment is activated.

### Dependency Build Problems

If `psycopg2` or other compiled packages fail during setup, use the Conda environment from `environment.yml`, which is the most reproducible path for this repository.

## Next Steps

- Continue with the [Quick Start](quickstart.md)
- Review the [Overview](../user-guide/overview.md)
- Customize providers and endpoints in the [Configuration Guide](../user-guide/configuration.md)
