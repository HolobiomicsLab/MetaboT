# MetaboT - AI-System for Metabolomics Data Exploration

A Streamlit-based web application for exploring and analyzing metabolomics data from the ENPKG 1,600 plant extract dataset.

## Overview

MetaboT is an AI-powered system designed to facilitate the exploration of metabolomics data. It integrates with OpenAI's GPT models and SPARQL endpoints to provide intelligent analysis and querying capabilities for metabolomics datasets.

## Features

- Interactive chat interface for querying metabolomics data
- Integration with OpenAI GPT models
- SPARQL endpoint connectivity for data retrieval
- Real-time data visualization
- File upload capabilities for custom data analysis
- Session management and data persistence
- Automated file cleanup system

## Project Structure

```
streamlit_webapp/
├── cleanup_files.py       # Utility for cleaning up temporary files
├── cleanup_database.py    # Database cleanup operations
├── postgres_database.py   # PostgreSQL database management
├── postgres_tool_database.py  # Tool-specific database operations
├── streamlit_app.py       # Main Streamlit application
├── streamlit_utils.py     # Utility functions for the Streamlit app
├── streamlit_workflow.py  # Workflow management
└── misc/                  # Miscellaneous resources
    ├── help.txt          # Help documentation
    ├── splash_text.txt   # Application splash text
    └── icons and logos   # Visual assets
```

## Prerequisites

- Python 3.x
- PostgreSQL database
- OpenAI API key
- Access to a SPARQL endpoint

## Environment Variables

The application requires the following environment variables:

- `DATABASE_URL`: PostgreSQL database connection string
- `OPENAI_API_KEY`: OpenAI API key
- `ADMIN_KEY`: Administrator access key
- `ACCESS_KEY`: General access key
- `ADMIN_OPENAI_KEY`: Administrator OpenAI API key
- `LANGCHAIN_API_KEY`: LangChain API key (optional)
- `CODEBOX_API_KEY`: Codebox API key (optional)

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up the PostgreSQL database and configure the environment variables.

3. Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```

## Usage

1. Launch the application and configure your API keys in the sidebar:
   - Set OpenAI API key
   - Configure SPARQL endpoint (default: ENPKG endpoint)
   - Optional: Set contributor key for additional features

2. Use the chat interface to:
   - Ask questions about metabolomics data
   - Upload custom files for analysis
   - View visualizations and results
   - Download analysis results

3. Available query examples:
   - Feature analysis across ionization modes
   - Chemical classification queries
   - Taxonomic analysis
   - Activity analysis against specific targets
   - Comparative analysis of features

## Database Management

The application uses PostgreSQL for:
- Session management
- Checkpointing
- Tool data storage
- Query results caching

Automatic cleanup is performed for:
- Temporary files (older than 1 hour)
- Database checkpoints (older than 24 hours)

## Contributing

For contributors with access keys, the application provides:
- Extended functionality
- Access to admin features
- Ability to log traces on LangSmith server

## License

[Include license information here]

## Support

[Include support contact information here]