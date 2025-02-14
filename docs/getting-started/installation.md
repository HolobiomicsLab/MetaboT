# Installation Guide

This guide will walk you through the process of installing MetaboT and its dependencies.

## Prerequisites

Before installing MetaboT, ensure you have the following prerequisites:

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/holobiomicslab/MetaboT.git
cd MetaboT
```

### 2. Create a Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other Python packages:

```bash
# Using conda (recommended)
conda env create -f environment.yml

# Or using venv
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=metabolomics
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: API Keys for external services
OPENAI_API_KEY=your_openai_api_key  # If using OpenAI services
```

### 2. SPARQL Endpoint Configuration

Edit `app/config/sparql.ini` to configure your SPARQL endpoint:

```ini
[sparql]
endpoint=http://your-sparql-endpoint:8890/sparql
graph=http://your-graph-uri
```

### 3. Data Conversion and Default Dataset

To use 🤖 MetaboT 🍵, your mass spectrometry processing and annotation results must first be converted into a knowledge graph format using the ENPKG tool. By default, MetaboT connects to the public ENPKG endpoint which hosts an open, annotated mass spectrometry dataset derived from a chemodiverse collection of **1,600 plant extracts**. This default dataset enables you to explore all features of MetaboT without the need for custom data conversion immediately. For more details on converting your own data, please refer to the [Experimental Natural Products Knowledge Graph library](https://doi.org/10.1021/acscentsci.3c00800) and the associated publication.

Edit `app/config/sparql.ini` to configure your SPARQL endpoint:

```ini
[sparql]
endpoint=http://your-sparql-endpoint:8890/sparql
graph=http://your-graph-uri
```

## Verify Installation

To verify your installation:

```bash
python -m pytest app/core/tests/
```

All tests should pass successfully.

## Common Issues and Solutions

### Issue: Database Connection Error

If you encounter database connection issues:

1. Ensure PostgreSQL is running
2. Verify database credentials in `.env`
3. Run the test connection script:
   ```bash
   python app/core/test_db_connection.py
   ```

### Issue: SPARQL Endpoint Connection

If SPARQL queries fail:

1. Check if the SPARQL endpoint is accessible
2. Verify endpoint configuration in `sparql.ini`
3. Ensure proper network access/firewall settings

## Next Steps

- Follow the [Quick Start Guide](quickstart.md) to begin using MetaboT
- Review the [Configuration Guide](../user-guide/configuration.md) for detailed setup options
- Check out [Example Usage](../examples/basic-usage.md) for practical applications

## Support

If you encounter any issues during installation:

1. Check our [GitHub Issues](https://github.com/holobiomicslab/MetaboT/issues) for similar problems
2. Create a new issue with detailed information about your setup and the error
3. Join our community discussions for help