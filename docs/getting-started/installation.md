# Installation Guide 🚀

This guide will walk you through the process of installing 🧪 MetaboT 🍵 and its dependencies.

---

## Prerequisites 📋

Before installing 🧪 MetaboT 🍵, ensure you have the following installed:

- **pip** (Python package installer) — [Install pip](https://pip.pypa.io/en/stable/installation/)
- **conda** — [Install Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- **Git** — [Install Git](https://git-scm.com/downloads)
- **LLM API Key** — Get an API key for your chosen language model (OpenAI, DeepSeek, or Claude)
- **WSL** (for Windows users) — [Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

---

## **Clone the Repository** 📥

```bash
git clone https://github.com/holobiomicslab/MetaboT.git
git checkout [dev](https://github.com/holobiomicslab/MetaboT/tree/dev)
cd MetaboT
```

## **Create and Activate the Conda Environment** ⚙️

   **For macOS:**
   ```bash
   conda env create -f environment.yml
   conda activate MetaboT
   ```

   **For Linux:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-dev build-essential
   conda env create -f environment.yml
   conda activate MetaboT
   ```

   **For Windows (using WSL):**

   1. Install WSL if you haven't already:
      ```bash
      wsl --install
      ```
   2. Open WSL and install the required packages:
      ```bash
      sudo apt-get update
      sudo apt-get install -y python3-dev build-essential
      ```
   3. Install Miniconda in WSL:
      ```bash
      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      bash Miniconda3-latest-Linux-x86_64.sh
      source ~/.bashrc
      ```
   4. Create and activate the conda environment:
      ```bash
      conda env create -f environment.yml
      conda activate MetaboT
      ```

---

## Install Dependencies 📦

```bash
pip install -r requirements.txt
```

---

## Environment Variables 🔑

Create a `.env` file in the [root directory](https://github.com/holobiomicslab/MetaboT) with the following variables:

```text
# Optional: API Keys for external services
OPENAI_API_KEY=your_openai_api_key  # If using OpenAI service
DEEPSEEK_API_KEY=your_deepseek_api_key # If using DeepSeek API service
OVHCLOUD_API_KEY=your_ovhcloud_api_key # If using the OVHcloud services 
```

---

## Language Model Configuration 🤖

By default, all agents in MetaboT use OpenAI models, but you can configure different models for each agent. The current implementation supports:
- OpenAI
- DeepSeek
- Claude (Anthropic)
- Llama (via OVHcloud)

### Adding New Models

To add a new model using LiteLLM:

1. Add a new section in `app/config/params.ini`:
```ini
[llm_litellm_your_model_name]
temperature=0.0
id=your-provider/model-name  # As specified in https://docs.litellm.ai/docs/providers
max_retries=3
```

2. Add your provider and API key mapping in `app/core/main.py`:
```python
API_KEY_MAPPING = {
    "deepseek": "DEEPSEEK_API_KEY",
    "ovh": "OVHCLOUD_API_KEY",
    "openai": "OPENAI_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "your-provider": "YOUR_PROVIDER_API_KEY"  # Add your mapping here
}
```

3. Modify the provider detection in `create_litellm_model` function:
```python
if model_id.startswith("deepseek"):
    provider = "deepseek"
elif model_id.startswith("gpt"):
    provider = "openai"
    model_name = f"openai/{model_id}"
elif model_id.startswith("your-prefix"):  # Add your model prefix detection
    provider = "your-provider"
```

The function automatically handles:

- Provider detection based on model ID prefix
- API key retrieval from environment variables
- Basic parameters (temperature, max_retries)
- Optional base URL configuration

### Configuring Models for Different Agents

To use different models for different agents, modify `app/config/langgraph.json`. In the agents section, specify `llm_choice` with the name of your model section from params.ini:

```json
{
  "agents": {
    "sparql_agent": {
      "llm_choice": "llm_litellm_your_model_name"
    },
    "validator_agent": {
      "llm_choice": "llm_litellm_different_model"
    }
  }
}
```

## SPARQL Endpoint Configuration 🌐

Configure your SPARQL endpoint exclusively by setting the <code>KG_ENDPOINT_URL</code> variable in your <code>.env</code> file.

---

## Verify Installation ✅

To verify the installation, execute the following command:

```bash
python app/tests/installation_test.py
```

This command initiates the agent workflow by constructing the RDF graph using the endpoint specified via the KG_ENDPOINT_URL variable in your .env file, instantiating the requisite language models, and executing one of the predefined standard queries. Successful execution confirms the proper configuration and integration of the system's core functionalities, including graph management and SPARQL query generation.

---

## Common Issues 🐞

#### Issue: SPARQL Endpoint Connection

If SPARQL queries fail:

1. Check if the SPARQL endpoint is accessible.

2. Verify that the <code>KG_ENDPOINT_URL</code> variable in your <code>.env</code> file is correctly set.

3. Ensure proper network access/firewall settings.

---

## Mass Spectrometry Data 🔬

By default, 🧪 MetaboT 🍵 connects to the public ENPKG endpoint which hosts an open, annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset enables you to explore all features of 🧪 MetaboT 🍵 without the need for custom data conversion immediately. To use 🧪 MetaboT 🍵 on your mass spectrometry data, the processed and annotated results must first be converted into a knowledge graph format using the ENPKG tool. For more details on converting your own data, please refer to the [*Experimental Natural Products Knowledge Graph library*](https://github.com/enpkg) and the [associated publication](https://doi.org/10.1021/acscentsci.3c00800).

Set your SPARQL endpoint by configuring the <code>KG_ENDPOINT_URL</code> variable in your <code>.env</code> file. If you are deploying a local endpoint that requires authentication, add the following variables to your <code>.env</code> file:

```text
SPARQL_USERNAME=your_username
SPARQL_PASSWORD=your_password
```

Additionally, to ensure the SPARQL queries generated accurately reflect the schema of your knowledge graph, you must provide detailed information about your knowledge graph’s structure and update the prompt settings in:
 
- <code>app/core/agents/validator/prompt.py</code>
- The SPARQL generation chain in <code>app/core/agents/sparql/tool_sparql.py</code>

---

## Support 🛠️

If you encounter any issues during installation:

1. Check our [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) for similar problems.
2. Create a new [issue](https://github.com/holobiomicslab/MetaboT/issues) with detailed information about your setup and the error.

---

**Next Steps**

- Follow the [Quick Start Guide](../quickstart/) to begin using 🧪 MetaboT 🍵.
- Review the [Configuration Guide](../../user-guide/configuration/) for detailed setup options.
- Check out [Example Usage](../../examples/basic-usage/) for practical applications.
