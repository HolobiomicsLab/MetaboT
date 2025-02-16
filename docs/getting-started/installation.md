# Installation Guide 🚀

This guide will walk you through the process of installing MetaboT and its dependencies.

---

## Prerequisites 📋

Before installing MetaboT, ensure you have the following installed:

- **pip** (Python package installer) — [Install pip](https://pip.pypa.io/en/stable/installation/)
- **conda** — [Install Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- **Git** — [Install Git](https://git-scm.com/downloads)
- **OpenAI API Key** — [Get your API key](https://platform.openai.com/api-keys)
- **WSL** (for Windows users) — [Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

---

### **Clone the Repository**

   ```bash
   git clone https://github.com/holobiomicslab/MetaboT.git
   git checkout [dev](https://github.com/holobiomicslab/MetaboT/tree/dev)
   cd MetaboT
   ```

### **Create and Activate the Conda Environment**

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


### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Environment Variables

Create a `.env` file in the [root directory](https://github.com/holobiomicslab/MetaboT) with the following variables:

```text
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=metabolomics
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: API Keys for external services
OPENAI_API_KEY=your_openai_api_key  # If using OpenAI services
```

---

### SPARQL Endpoint Configuration

Edit [`app/config/sparql.ini`](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/sparql.ini) to configure your SPARQL endpoint:

```ini
[sparql]
endpoint=http://your-sparql-endpoint:8890/sparql
graph=http://your-graph-uri
```


---

### Verify Installation

To verify your installation:

```bash
python -m pytest app/core/tests/
```

All tests should pass successfully.

---

### Common Issues and Solutions

#### Issue: Database Connection Error

If you encounter database connection issues:
1. Ensure PostgreSQL is running.
2. Verify database credentials in `.env`.
3. Run the test connection script:
   ```bash
   python [app/core/test_db_connection.py
   ```

#### Issue: SPARQL Endpoint Connection

If SPARQL queries fail:
1. Check if the SPARQL endpoint is accessible.
2. Verify endpoint configuration in `sparql.ini`.
3. Ensure proper network access/firewall settings.

---

---

## Mass Spectrometry Data 🔬

To use MetaboT, your mass spectrometry processing and annotation results must first be converted into a knowledge graph format using the ENPKG tool. By default, MetaboT connects to the public ENPKG endpoint which hosts an open, annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset enables you to explore all features of MetaboT without the need for custom data conversion immediately. For more details on converting your own data, please refer to the [*Experimental Natural Products Knowledge Graph library*](https://github.com/enpkg) and the [associated publication](https://doi.org/10.1021/acscentsci.3c00800).

Edit [`app/config/sparql.ini`](https://github.com/holobiomicslab/MetaboT/blob/main/app/config/sparql.ini) to configure your SPARQL endpoint:

```ini
[sparql]
endpoint=http://your-sparql-endpoint:8890/sparql
graph=http://your-graph-uri
```

---

## Support 🛠️

If you encounter any issues during installation:

1. Check our [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) for similar problems.
2. Create a new [Issues](https://github.com/holobiomicslab/MetaboT/issues)  with detailed information about your setup and the error.

---

**Next Steps**

- Follow the [Quick Start Guide](../quickstart/) to begin using MetaboT.
- Review the [Configuration Guide](../../user-guide/configuration/) for detailed setup options.
- Check out [Example Usage](../../examples/basic-usage/) for practical applications.
