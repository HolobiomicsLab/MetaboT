from io import BytesIO
import json
from pathlib import Path
import re
import os
import uuid
from zipfile import ZipFile
import plotly.graph_objects as go

from MetaboT.app.core.main import llm_creation
from MetaboT.app.core.workflow.langraph_workflow import create_workflow
from MetaboT.app.core.memory.database_manager import tools_database, memory_database
from MetaboT.app.core.session import (
    create_user_session,
    initialize_session_context,
    initialize_thread_id,
)
from langchain_core.messages import HumanMessage
# Initialize workflow and database
langgraph_app = None
tools_db = tools_database()
#memory_db = memory_database()


def initialize_workflow(session_id: str, api_key: str, endpoint_url: str):
    """
    Initialize the workflow with the given parameters.

    Args:
        session_id (str): The session ID for the workflow
        api_key (str): The OpenAI API key
        endpoint_url (str): The endpoint URL for the knowledge graph

    Returns:
        The initialized workflow
    """
    global langgraph_app

    # Create user session and initialize context
    create_user_session(session_id)
    initialize_session_context(session_id)
    thread_id = f"{session_id}{uuid.uuid4().hex[:4]}"
    initialize_thread_id(thread_id)

    # Initialize database
    try:
        pass
        #tools_db.initialize_db()
    except Exception as e:
        print(f"Database initialization failed: {e}")

    # Create workflow

    models = llm_creation()
    langgraph_app = create_workflow(
        models=models,  # Will be configured by the workflow
        session_id=session_id,
        api_key=api_key,
        endpoint_url=endpoint_url,
        evaluation=False,
    )

    return langgraph_app

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
    print(f"File paths extracted from the database: {filepaths}")

    for filepath in filepaths:
        try:
            # Open and read the file content
            with open(filepath, 'r') as file:
                json_content = file.read()
            print(f"JSON content read from file: {json_content}")

            # Clean the JSON content of any specific unwanted URLs
            fixed_content = re.sub(r'https://enpkg\.commons-lab\.org/kg/', '', json_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'https:\\u002f\\u002fenpkg\.commons-lab\.org\\u002fkg\\u002f', '', fixed_content, flags=re.IGNORECASE)
            
            # Load the JSON data
            json_data = json.loads(fixed_content)
            print(f"JSON data loaded successfully: {json_data}")
            
            # Create the Plotly figure
            fig = go.Figure(json_data)
            filename = os.path.basename(filepath)
            print(f"Filename extracted from file path: {filename}")

            # Save the figure as a PNG file
            session_temp_dir = create_user_session(session_id, user_session_dir=True)
            output_file_path = os.path.join(session_temp_dir, f"{os.path.splitext(filename)[0]}.png")
            print(f"Output file path constructed: {output_file_path}")

            fig.write_image(output_file_path)
            print(f"Visualization PNG saved at: {output_file_path}")

            return fig

        except Exception as e:
            print(f"Failed to process file {filepath}: {e}")
            continue  # Continue to the next file if there's an issue with the current one

    print("No valid JSON files processed.")
    return None


def process_workflow_request(
    prompt: str, session_id: str, api_key: str, endpoint_url: str
):
    """
    Process a request using the workflow.

    Args:
        prompt (str): The user prompt
        session_id (str): The session ID
        api_key (str): The OpenAI API key
        endpoint_url (str): The endpoint URL for the knowledge graph

    Returns:
        Generator for the workflow response
    """
    global langgraph_app

    # Initialize workflow if not already initialized
    if langgraph_app is None:
        langgraph_app = initialize_workflow(session_id, api_key, endpoint_url)

    # Add interaction to tools database
    tools_db.add_interaction()

    # Process the request
    for event in langgraph_app.stream(
        {"messages": [HumanMessage(content=prompt)]},
        {"configurable": {"thread_id": session_id}},
    ):
        for k, v in event.items():
            data = {
                "type":0,
                "content":None,
                "typeContent":None,
                "agent":None
            }
            if k != "__end__":
                data["agent"] = k
                if k == 'supervisor':
                    if 'next' in v and v['next'] == "Sparql_query_runner":
                        data["content"] = "*The Agent Supervisor is Calling the Sparql Query Runner Agent to retrieve your information from ENPKG...*\n"
                    elif 'next' in v and v['next'] != "FINISH":
                        agent_name = v['next']
                        data["content"] = f"*Agent Supervisor is calling {agent_name}.*\n"
                    elif 'next' in v and v['next'] == 'FINISH':
                        break
                    data["typeContent"] = "text"
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    content = v['messages'][0].content
                    emoji_map = {
                        'Entry_agent': '👋',
                        'Validator_agent': '✅',
                        'ENPKG_agent':'🧠',
                        'Sparql_query_runner':'🔍',
                        'Interpreter_agent':'📊'
                    }
                    emoji = emoji_map[k]

                    data["content"] = f"* ##### {k.replace('_',' ')} {emoji} \n{content}\n"
                    data["typeContent"] = "text"
                    yield f"data: {json.dumps(data)}\n\n"
                    if k == "Interpreter_agent":
                        fig = plotly_from_interpreter(session_id, "tool_interpreter")
                        if fig:
                            data["content"] = fig
                            data["typeContent"] = "visualization"
                            yield f"data: {json.dumps(data)}\n\n"
                
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