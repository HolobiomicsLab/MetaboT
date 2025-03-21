#streamlit utils
import os
import re
import streamlit as st
import openai
from openai import OpenAI
import requests
import logging
from pathlib import Path
import json
import plotly.graph_objects as go
from app.core.session import setup_logger, create_user_session
from zipfile import ZipFile
from io import BytesIO
from contextvars import ContextVar
import json
from app.core.memory.database_manager import tools_database

logger = setup_logger(__name__)

# This will give you the directory containing the current file
current_file_directory = Path(__file__).parent

def is_true(value):
    """
    Check if a given string value represents a true value.

    Args:
    value (str): The string to check.

    Returns:
    bool: True if the string represents a true value, False otherwise.
    """
    # Define a set of string representations of true
    true_values = {'true', '1', 't', 'y', 'yes'}
    # Normalize the input to lower case to make the check case insensitive
    return value.lower() in true_values

def print_files_in_directory(directory):
    """Prints the names of all files in the given directory using pathlib."""
    # Ensure directory is a Path object
    directory = Path(directory)

    # List directory contents and print file names
    for item in directory.iterdir():
        if item.is_file():
            print(item.name)  # item.name gives just the file name, not the full path

def create_zip_buffer(session_id):
    """
    Create a zip buffer containing files in the session directory, optionally including app.log.

    Parameters:
    - session_id (str): The session ID to create the zip buffer for.

    Returns:
    - BytesIO: The zip buffer.
    """
    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, 'w') as zip_file:
        zip_session_files(zip_file, session_id, prefix="session_files", include_log=True)

    zip_buffer.seek(0)
    return zip_buffer

def zip_session_files(zip_obj, session_id, prefix="", include_log=False):
    """
    Zip all files in the session directory into the given zip file object.

    Parameters:
    - zip_obj (ZipFile): The ZipFile object to write the files to.
    - session_id (str): The session ID to zip the files from.
    - prefix (str): The prefix to add to the file paths within the zip archive.
    - include_log (bool): Whether to include the app.log file.
    """

    session_directory = create_user_session(session_id, user_session_dir=True)
    log_file_path = session_directory / "kgbot.log"

    def add_to_zip(item, prefix):
        if item.is_file():
            # Exclude app.log if include_log is False
            if not include_log and item == log_file_path:
                return
            archive_name = Path(prefix) / item.name
            zip_obj.write(item, arcname=str(archive_name))
        elif item.is_dir():
            for sub_item in item.iterdir():
                add_to_zip(sub_item, Path(prefix) / item.name)

    for item in session_directory.iterdir():
        add_to_zip(item, prefix)

def test_openai_key(user_provided_key):
    """
    Validates the provided OpenAI API key by attempting a test API call.

    Parameters:
    - api_key (str): The OpenAI API key to validate.

    Returns:
    - bool: True if the API key is valid and has access to the specified model, False otherwise.
    """

    client = OpenAI(api_key=user_provided_key)

    try:
        # Test call to OpenAI API, adapted to API changes in Nov 2023
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Test"}
            ]
        )
        if completion:
            return True
        else:
            return False
      
    # Handle connection error, e.g. check network or log
    except openai.APIConnectionError as e:
        st.error(f"OpenAI API request failed to connect: {e}")
        return False
    
    # Handle timeout error, e.g. retry or log
    except openai.APITimeoutError as e:
        st.error(f"OpenAI API request timed out: {e}")
        return False
    
    # Handle authentication error, e.g. check credentials or log
    except openai.AuthenticationError as e:
        st.error(f"OpenAI API request was not authorized: {e}")
        return False

    # Handle invalid request error, e.g. validate parameters or log
    except openai.BadRequestError as e:
        st.error(f"OpenAI API request was invalid: {e}")
        return False
    
    # Handle conflicting request errors
    except openai.ConflictError as e:
        st.error(f"OpenAI API request had a conflict error: {e}")
        return False
    
    # Handle interal server errors, e.g, issue on OPENAi
    except openai.InternalServerError as e:
        st.error(f"OpenAI API request had a conflict error: {e}")
        return False

    # Handle interal server errors, e.g, issue on OPENAi
    except openai.NotFoundError as e:
        st.error(f"OpenAI API requested source doesn't exist: {e}")
        return False

    # Handle interal server errors, e.g, issue on OPENAi
    except openai.PermissionDeniedError as e:
        st.error(f"The provided OpenAI API key doesn't have access to GPT-4: {e}")
        return False
    
    #Handle rate limit error, e.g. wait or log
    except openai.RateLimitError as e:
        st.error(f"OpenAI API request exceeded rate limit: {e}")
        pass

    # Handle other API errors
    except openai.APIError as e:
        st.error(f"OpenAI API returned an API Error: {e}")
        return False
    
def test_sparql_endpoint(endpoint):
    """
    Tests the validity of a SPARQL endpoint by sending a simple ASK query.

    Parameters:
    - endpoint (str): The URL of the SPARQL endpoint to test.

    Returns:
    - bool: True if the endpoint is valid and responsive, False otherwise.
    """
    test_query = {"query": "ASK {}"}
    headers = {"Accept": "application/sparql-results+json"}
    try:
        response = requests.get(endpoint, params=test_query, headers=headers, timeout=15)
        response.raise_for_status()  # Ensures HTTP request was successful
        # Validate response format
        if response.json() is not None:
            return True
        else:
            st.sidebar.warning("The endpoint did not return a valid SPARQL result.")
            return False
    except requests.RequestException as e:
        st.sidebar.warning(f"Failed to connect to the endpoint: {e}")
        return False
    
def check_characters_api_key(input):
    """
    Test if the user input contains only allowed characters for api_key, including alphanumeric, dash and underscore.
    Checking the validity of the user input can prevent unexpected errors of using non-usual characters

    Parameter:
     - input: The password input or any value provided by the user

    Returns: 
     - bool: True if valid, false if don't
    """
    valid_chars_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

    if valid_chars_pattern.match(input):
        return True
    else:
        return False

def plotly_from_interpreter(session_id, tool):
    """
    Generates a Plotly figure from JSON data read from file paths stored in a context variable 
    and saves it as a PNG file.

    Args:
        session_id (str): The unique session ID for identifying the output file.
        tool (str): The name of the tool that generated the files/

    Returns:
        plotly.graph_objs.Figure: The Plotly figure generated from the JSON data.
    """
    # Assuming 'filepaths' is a list of file paths available as a context variable

    db_manager = tools_database()
    interpreter_output = db_manager.get(tool)  # Get all file paths from the database associated with the tool_interpreter

    output_json = json.loads(interpreter_output)
    filepaths = output_json['output']['paths']
    logger.info(f"File paths extracted from the database: {filepaths}")

    for filepath in filepaths:
        try:
            # Open and read the file content
            with open(filepath, 'r') as file:
                json_content = file.read()
            logging.info(f"JSON content read from file: {json_content}")

            # Clean the JSON content of any specific unwanted URLs
            fixed_content = re.sub(r'https://enpkg\.commons-lab\.org/kg/', '', json_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'https:\\u002f\\u002fenpkg\.commons-lab\.org\\u002fkg\\u002f', '', fixed_content, flags=re.IGNORECASE)
            
            # Load the JSON data
            json_data = json.loads(fixed_content)
            logging.info(f"JSON data loaded successfully: {json_data}")
            
            # Create the Plotly figure
            fig = go.Figure(json_data)
            filename = os.path.basename(filepath)
            logging.info(f"Filename extracted from file path: {filename}")

            # Save the figure as a PNG file
            session_temp_dir = create_user_session(session_id, user_session_dir=True)
            output_file_path = os.path.join(session_temp_dir, f"{os.path.splitext(filename)[0]}.png")
            logging.info(f"Output file path constructed: {output_file_path}")

            fig.write_image(output_file_path)
            logging.info(f"Visualization PNG saved at: {output_file_path}")

            return fig

        except Exception as e:
            logging.error(f"Failed to process file {filepath}: {e}")
            continue  # Continue to the next file if there's an issue with the current one

    logging.info("No valid JSON files processed.")
    return None

def get_spectrum_image(tool):

    db_manager = tools_database()

    interpreter_output = db_manager.get(tool)

    output_json = json.loads(interpreter_output)
    filepaths = output_json['output']['paths']
    logger.info(f"File paths extracted from the database: {filepaths}")

    return filepaths

def check_tools_interpreter(tool):
    db_manager = tools_database()

    content = db_manager.get(tool)

    if content is None:
        return False
    else:
        return True

def new_process_langgraph_output(k, v, session_id):
    
    contents = []

    if k != "__end__":
        if k == "supervisor":
            if 'next' in v and v['next'] == "Sparql_query_runner":
                contents.append({"type": "text", "content": "The Agent Supervisor is Calling the Sparql Query Runner Agent to retrieve your information from ENPKG... \n\n"})
            elif 'next' in v and v['next'] != "FINISH":
                agent_name = v['next']
                contents.append({"type": "text", "content": f"Agent Supervisor is calling {agent_name}. \n\n"})
            elif 'next' in v and v['next'] == "FINISH":
                contents.append({"type": "text", "content": "Chain finished"})
        elif k == "Entry_agent":
            content = v['messages'][0].content
            contents.append({"type": "text", "content": f"Entry agent: {content}. \n\n"})
        elif k == "Validator_agent":
            content = v['messages'][0].content
            contents.append({"type": "text", "content": f"Validator agent: {content}. \n\n"})
        elif k == "ENPKG_agent":
            content = v['messages'][0].content
            contents.append({"type": "text", "content": f"ENPKG: {content}. \n\n"})
        elif k == "Sparql_query_runner":
            content = v['messages'][0].content
            contents.append({"type": "text", "content": f"Sparql Query Runner: {content}. \n\n"})
        elif k == "Interpreter_agent":
            content = v['messages'][0].content
            contents.append({"type": "text", "content": f"Interpreter Agent: {content}. \n\n"})

            has_interpreter_content = check_tools_interpreter("tool_interpreter")
            if has_interpreter_content:
                fig = plotly_from_interpreter(tool="tool_interpreter", session_id=session_id)
                if fig is not None:
                    contents.append({"type": "visualization", "content": fig})

            has_spectra_content = check_tools_interpreter("tool_spectrum")
            if has_spectra_content:
                fig_spectra = get_spectrum_image("tool_spectrum")
                if fig_spectra is not None:
                    contents.append({"type": "spectra", "content": fig_spectra})


    return contents