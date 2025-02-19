# Setting up Session for streamlit app
# It's ugly but it has to be done in the very beginning of the script

import streamlit as st
import os
from uuid import uuid4
import sys
sys.path.insert(0, '/Users/yzhouchen001/Desktop/research/kgbot_webapp')
# print(sys.path)
from app import core
from app.core.session import create_user_session, initialize_session_context, initialize_thread_id, setup_logger

if "session_id" not in st.session_state:
    st.session_state.session_id = create_user_session()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(st.session_state.session_id) + str(uuid4().hex[:4])

if "session_temp_dir" not in st.session_state:
    st.session_state.session_temp_dir = create_user_session(st.session_state.session_id, user_session_dir=True)

if "user_input_dir" not in st.session_state:
    st.session_state.user_input_dir = create_user_session(st.session_state.session_id, input_dir=True)

initialize_session_context(st.session_state.session_id)
initialize_thread_id(st.session_state.thread_id)

if "logger" not in st.session_state:
    logger = setup_logger(__name__)
    st.session_state.logger = logger

# Following normal code execution    
    
import os
import tempfile
from pathlib import Path
import logging.config
import logging
import time
from openai import OpenAI
from langchain_core.messages import HumanMessage
from langsmith import Client
from streamlit_modal import Modal
import streamlit.components.v1 as components
from app.core.memory.database_manager import tools_database, memory_database
from langchain.callbacks.manager import tracing_v2_enabled
from streamlit_webapp.streamlit_utils import check_characters_api_key, test_sparql_endpoint, test_openai_key, new_process_langgraph_output, create_zip_buffer, is_true
from app.core.workflow.langraph_workflow import create_workflow

# Configuring page
st.set_page_config(
    page_title="MetaboT - An AI-System for Metabolomics Data Exploration)", 
    page_icon="misc/icon.png", 
    layout="wide", 
    initial_sidebar_state="auto", 
    menu_items=None
)

# Help text
help_path = Path(__file__).parent / "misc" / "help.txt"
with help_path.open("r") as file:
    help = file.read()

# Splash text
splashtext_path = Path(__file__).parent / "misc" / "splash_text.txt"
with splashtext_path.open("r") as file:
    splash_text = file.read()

# Get the variables set as the environmental variables in Heroku Keys
contributor_key = os.environ.get("CONTRIBUTOR_KEY")
contributor_openai_key = os.environ.get("CONTRIBUTOR_OPENAI_KEY")
contributor_langsmith_key = os.environ.get("LANGCHAIN_API_KEY")

if "tools_database" not in st.session_state:
    st.session_state.tools_database = tools_database()

if "contributor_key_expander" not in st.session_state:
    st.session_state.contributor_key_expander = False

if "contributor_key" not in st.session_state:
    st.session_state.contributor_key = False

if "OPENAI_API_KEY" not in st.session_state:
    st.session_state.OPENAI_API_KEY = None

if "openai_key_success" not in st.session_state:
    st.session_state.openai_key_success = False

if "openai_key_expander" not in st.session_state:
    st.session_state.openai_key_expander = True

if "endpoint_url" not in st.session_state:
    st.session_state.endpoint_url = None

if "endpoint_key_expander" not in st.session_state:
    st.session_state.endpoint_key_expander = False

if "endpoint_url_success" not in st.session_state:
    st.session_state.endpoint_url_success = False

if "question_submitted" not in st.session_state:
    st.session_state.question_submitted = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "preselected_question" not in st.session_state:
    st.session_state.preselected_question = None

if "set_standard_endpoint" not in st.session_state:
    st.session_state.set_standard_endpoint = True

if "langgraph_app_created" not in st.session_state:
    st.session_state.langgraph_app_created = False

if "langgraph_app" not in st.session_state:
    st.session_state.langgraph_app = None

if "langsmith_allowed" not in st.session_state:
    st.session_state.langsmith_allowed = False

if "figures" not in st.session_state:
    st.session_state.figures = []

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if "prompt" not in st.session_state:
    st.session_state.prompt = ""

if "memory" not in st.session_state:
    st.session_state.memory = memory_database()

#Header configuration
st.title("MetaboT - An AI-system for Metabolomics Data Exploration")
subheader_markdown = """
Prototype for the [ENPKG 1,600 plant extract dataset](https://doi.org/10.1021/acscentsci.3c00800)
"""
st.markdown(subheader_markdown)
st.markdown("---")

# Sidebar Configuration for User Inputs
with st.sidebar:

    st.markdown("---")
    st.subheader("Please read:")
    st.markdown("Link one")
    st.markdown("Link two")
    st.markdown("---")

    # OpenAI API Key Input and Validation
    with st.expander("Set a OpenAI API Key", expanded=st.session_state.openai_key_expander):
        with st.form(key='api_key_form'):
            st.title('🧠 OpenAI API Key Configuration')
            st.markdown('Enter your OpenAI API Key ([see here for obtaining a key](https://platform.openai.com/account/api-keys)).')
            # User input for the OpenAI API key
            user_provided_key = st.text_input('OpenAI API Key:', type='password')
            validate_key_button = st.form_submit_button("Validate API Key")

            # Validate and use the OpenAI API key
            if validate_key_button and user_provided_key:

                # Checking the validity of the characters used in the API key
                if check_characters_api_key(user_provided_key) == True:

                    if test_openai_key(user_provided_key) == True:
                        st.session_state.openai_key_success = True
                        st.session_state["OPENAI_API_KEY"]=user_provided_key
                        st.sidebar.success("Your OpenAI API key is valid and set!")
                        st.session_state.logger.info("OpenAI API Key set")
                        st.session_state.openai_key_expander = False
                    else:
                        st.session_state.openai_key_success = False

                else:
                    st.error("Please check the provided API Key. It must contain only alphanumeric, dash or underscores.")
                    st.session_state.logger.error("Invalid API Key provided")

    # SPARQL Endpoint Configuration
    with st.expander("Set a custom SPARQL Endpoint", expanded=st.session_state.endpoint_key_expander):
        with st.form(key='endpoint_form'):
            st.title('🔗 SPARQL Endpoint Configuration')

            # User input for the SPARQL endpoint URL
            user_endpoint = st.text_input("Enter the SPARQL endpoint URL:", value="https://enpkg.commons-lab.org/graphdb/repositories/ENPKG")
            validate_endpoint_button = st.form_submit_button("Validate Endpoint")

            # Validate and set the SPARQL endpoint URL
            if validate_endpoint_button:
                endpoint_url = user_endpoint

                # Test and provide feedback on the SPARQL endpoint validation
                if endpoint_url and test_sparql_endpoint(endpoint_url):
                    st.sidebar.success("Endpoint validated and set!")
                    st.session_state.logger.info(f"Custom endpoint set: {endpoint_url}")
                    st.session_state.endpoint_url = endpoint_url
                    st.session_state.endpoint_url_success = True
                    st.session_state.set_standard_endpoint = False
                    st.session_state.endpoint_key_expander = False
                else:
                    st.session_state.endpoint_url_sucess = False
                    st.sidebar.error("Failed to validate the endpoint. Please check the URL and try again.")
                    st.session_state.logger.error("Failed to validate the endpoint. Please check the URL and try again.")

    with st.expander("Set a Langsmith API Key", expanded=False):
        if st.session_state.openai_key_success == True:
            with st.form(key="langsmith_api_key_form"):
                st.title("🦜 Langsmith API Key")

                # User input for the langsmith key. 
                user_langmisth_api_key = st.text_input("If you have a LangSmith API Key, please inform it here", type="password")
                validate_langsmith_button = st.form_submit_button("Validate key")

                if validate_langsmith_button:
                    
                    if check_characters_api_key(user_langmisth_api_key) == True:
                        os.environ["LANGCHAIN_TRACING_V2"] = "true"
                        os.environ["LANGCHAIN_PROJECT"] = f"MetaboT - Streamlit" #Please update the name here if you want to create a new project for separating the traces. 
                        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
                        os.environ["LANGCHAIN_API_KEY"] = user_langmisth_api_key
                        client_langsmith = Client()
                        st.session_state.langsmith_allowed = True
                        st.sidebar.success("Your LangmSmit API Key is set! Your traces are being logged on the LangSmith server now")
                    else:
                        st.error("Please check the provided API Key. It must contain only alphanumeric, dash or underscores.")
        else:
            st.error("Please provide a valid OpenAI API Key first.")

    with st.expander("Set a contributor key", expanded=st.session_state.contributor_key_expander):
        with st.form(key="contributor_key_form"):
            st.title("🙏 Contributor key")

            # User input for the contributor key
            user_contributor_key = st.text_input("If you recieved a contributor key, please inform it here:", type="password")
            validate_contributor_key_button = st.form_submit_button("Validate key")

            if validate_contributor_key_button:
                if user_contributor_key == contributor_key:
                    st.session_state.logger.info("Contributor key validated")
                    st.session_state.openai_key_success = True
                    st.session_state.contributor_key = True
                    st.session_state.openai_key_expander = False
                    st.session_state.contributor_key_expander = False
                    st.session_state["OPENAI_API_KEY"] = contributor_openai_key
                    st.sidebar.success("Your contributor key is set! This includes access to exclusive features and a valid OpenAI Key on the house")
                    os.environ["LANGCHAIN_TRACING_V2"] = "true"
                    os.environ["LANGCHAIN_PROJECT"] = f"MetaboT Contributor Key - Streamlit" #Please update the name here if you want to create a new project for separating the traces.
                    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
                    os.environ["LANGCHAIN_API_KEY"] = contributor_langsmith_key
                    client_langsmith = Client()
                    st.session_state.langsmith_allowed = True
                else:
                    st.error("The provided key was not found. Please make sure the key provided is correct.")
                    st.session_state.logger.error("Contributor key not valid. Please check the key provided.")
                    
    if st.session_state.langgraph_app_created == True:

        ins_modal=Modal("Help to MetaboT", key="help")
        open_ins_modal = st.button("Help", use_container_width=True, disabled=st.session_state.is_processing)
        if open_ins_modal:
            ins_modal.open()

        if ins_modal.is_open():
            with ins_modal.container():
                st.write(help)

        download = st.download_button(
            label="Download files",
            data=create_zip_buffer(st.session_state.session_id),
            file_name="metabot_files.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=st.session_state.is_processing
        )

        clear_modal = Modal("Clear conversation data", key="clear")
        open_modal = st.button("Clear conversation data", use_container_width=True, disabled=st.session_state.is_processing)
        if open_modal:
            clear_modal.open()

        if clear_modal.is_open():
            with clear_modal.container():
                st.write("Clearing the chat history will delete all conversation history generated during the interaction with the MetaboT and restart the app. Please make sure you finished all questions on this topic before clearing the chat history.")
                clear = st.button("I understood.")
                if clear:
                    st.session_state.messages = []
                    st.session_state.thread_id = str(st.session_state.session_id)+str(uuid4().hex[:4])
                    initialize_thread_id(st.session_state.thread_id)
                    st.session_state.langgraph_app_created = False
                    clear_modal.close()
                    st.session_state.logger.info("Chat history cleared. App restarted.")
                    st.rerun()

    # Defining ENKPG as the Standard endpoint. Using session_state to control either
    if st.session_state.set_standard_endpoint == True:
        if test_sparql_endpoint("https://enpkg.commons-lab.org/graphdb/repositories/ENPKG") == True:
            st.session_state.endpoint_url = "https://enpkg.commons-lab.org/graphdb/repositories/ENPKG"
            st.session_state.endpoint_url_success = True
            st.sidebar.success("ENPKG Endpoint set")
            st.session_state.logger.info("ENPKG Endpoint set")
    else:
        pass

    st.markdown("---")
    st.subheader("Holobiomics Lab - CNRS, Université Côte d'Azur, Interdisciplinary Institute for Artificial Intelligence (3iA) Côte d'Azur")
    holobiomics_logo_path = str(Path(__file__).parent / "misc" / "HolobiomicsLab_graphics_v1_logos_small.png")
    st.image(holobiomics_logo_path, use_column_width=True)

if st.session_state.openai_key_success == False and st.session_state.endpoint_url_success == False:
    st.warning("You haven't provided a valid OpenAI API key and validated the connection to the endpoint. You need to provide a valid OpenAI API Key and connect to an Endpoint server. If you already tried to connect to an endpoint and it was unsucessful, there might be a connection problem. Please investigate further or come back later")
    with st.expander("", expanded=True):
        st.write(splash_text)

if st.session_state.openai_key_success == False and st.session_state.endpoint_url_success == True:
    st.warning("You haven't provided a valid OpenAI API key. A valid OpenAI Key is needed to use the MetaboT. ")
    with st.expander("", expanded=True):
        st.write(splash_text)

if st.session_state.openai_key_success == True and st.session_state.endpoint_url_success == False:
    st.warning("You're currently not connected to the endpoint. This can be due to error in the URL endpoint or the endpoint server not connecting. Please investigate further or come back later")
    with st.expander("", expanded=True):
        st.write(splash_text)

if st.session_state.openai_key_success == True and st.session_state.endpoint_url_success == True:
    if st.session_state.langgraph_app_created == False:
        st.warning("Initializing the LangGraph... Please wait")
        st.session_state.logger.info("Initializing the LangGraph")
        try:
            st.session_state.langgraph_app = create_workflow(session_id=st.session_state.session_id, api_key=st.session_state.OPENAI_API_KEY, endpoint_url=st.session_state.endpoint_url)
            st.session_state.langgraph_app_created = True
            st.session_state.logger.info("LangGraph initialized")
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred while initializing the LangGraph: {e}")
            st.session_state.logger.error(f"An error occurred while initializing the LangGraph: {e}")

    else:
        # Variables to track submission status of predefined and custom question
        select_submit_clicked = False
        custom_submit_clicked = False

        with st.expander("Input your own file", expanded=False):
            user_files = st.file_uploader("Choose your files", accept_multiple_files=True)
            if user_files:
                filenames = [file.name for file in user_files]
                try:
                    for file in user_files:
                        file_path = st.session_state.user_input_dir / file.name
                        with file_path.open("wb") as f:
                            f.write(file.getbuffer())
                    st.success(f"File(s) uploaded successfully: {filenames}")
                    st.session_state.logger.info(f"File(s) uploaded successfully: {filenames}")
                except Exception as e:
                    st.error(f"An error occurred while processing the file: {e}")

        with st.expander ("Try one our standard questions:", expanded=False):
        # Form for selecting a predefined question
            with st.form(key="select_form"):
                # Dynamically generated list of questions for user selection
                options = [
                    "How many features (pos ionization and neg ionization modes) have the same SIRIUS/CSI:FingerID and ISDB annotation by comparing the InCHIKey2D of the annotations?",
                    "Which extracts have features (pos ionization mode) annotated as the class, aspidosperma-type alkaloids, by CANOPUS with a probability score above 0.5, ordered by the decreasing count of features as aspidosperma-type alkaloids? Group by extract and provide a bar chart.",
                    "Provide the wikidata ids of the chemical entities annotated by SIRIUS for Tabernaemontana coffeoides seeds extract taxon obtained in positive mode which are also reported in the Tabernaemontana genus in Wikidata.",
                    "What are the Wikidata IDs of chemical entities that have ChEMBL activity against Trypanosoma cruzi?",
                    "Filter the pos ionization mode features of the Melochia umbellata taxon annotated as [M+H]+ by SIRIUS to keep the ones for which a feature in neg ionization mode is detected with the same retention time (+/- 3 seconds) and a mass corresponding to the [M-H]- SIRIUS adduct (+/- 5ppm). Provide the features and retention time.",
                    "For features from the Melochia umbellata taxon in pos ionization mode with SIRIUS annotations, get the ones for which a feature in neg ionization mode with the same retention time (+/- 3 seconds) has the same SIRIUS annotation by comparing the InCHIKey 2D. Return the features, retention times, and InChIKey2D",
                    "How many features annotated as 'Tetraketide meroterpenoids' by CANOPUS are found for each submitted taxon and extract in database?",
                    ]
                selected_option = st.selectbox("Please select one:", options)
                select_submit_clicked = st.form_submit_button("Submit Selected Question")
                if select_submit_clicked:
                    # Store the selected question for processing
                    st.session_state["preselected_question"] = selected_option

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):

                # Use st.text for proper new line handling
                st.write(message["content"])
                if message['url']:
                    # Render URL separately to handle it as clickable link
                    st.markdown(message['url'], unsafe_allow_html=True)

                # Check if there's an associated figure index
                if isinstance(message["image"], int):  # Using int check to identify figure indexes
                    # Retrieve and display the figure
                    fig = st.session_state.figures[message["image"]]
                    st.plotly_chart(fig)

                if isinstance(message["error"], str):
                    st.error(message["error"])

        # Build a if to block the buttons from being clicked while the question is running
        if prompt := st.chat_input("Ask MetaboT anything") or select_submit_clicked:
            st.session_state.is_processing = True
            if st.session_state["preselected_question"] != None:
                prompt = st.session_state["preselected_question"]
            st.session_state.prompt = prompt
            st.session_state.messages.append({"role": "user", "content": st.session_state.prompt, "image": "", "url": "", "error": None})
            st.session_state.logger.info(f"User question: {prompt}")
            st.rerun()

        # Starting the prompt    
        if st.session_state.is_processing == True:

            st.session_state.tools_database.add_interaction()

            with st.chat_message("assistant"):

                output_history = ""
                fig = None
                fig_index = ""
                error_message = None

                try:
                    if st.session_state.langsmith_allowed == True:
                        with tracing_v2_enabled("MetaboT Testing - Streamlit Testing") as cb:
                            for event in st.session_state.langgraph_app.stream({"messages": [HumanMessage(content=st.session_state.prompt)]}, {"configurable": {"thread_id": st.session_state.session_id}}):
                                for k, v in event.items():
                                    processed_outputs = new_process_langgraph_output(k=k, v=v, session_id=st.session_state.session_id)
                                    for content_dict in processed_outputs:  # Correct variable name used here
                                        if content_dict["type"] == "text":
                                            text_output = content_dict["content"]
                                            st.write(text_output)
                                            st.session_state.logger.info(text_output)
                                            output_history += text_output
                                        elif content_dict["type"] == "visualization":
                                            fig = content_dict["content"]
                                            try:
                                                st.plotly_chart(fig)
                                            except Exception as e:
                                                st.error(f"An error occurred while plotting the figure: {e}. Please check the log file for more information.")
                                            # Store the figure in the session state and save the index
                                            fig_index = len(st.session_state.figures)
                                            st.session_state.figures.append(fig)

                            url = cb.get_run_url()
                            url_message = f"View complete log in [LangSmith]({url})"
                            st.session_state.logger.info(url_message)
                            st.write("\n" + url_message, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": output_history, "image": fig_index, "url": url_message, "error": None})
                            time.sleep(0.5)

                    else:
                        for event in st.session_state.langgraph_app.stream({"messages": [HumanMessage(content=st.session_state.prompt)]}, {"configurable": {"thread_id": st.session_state.session_id}}):
                            for k, v in event.items():
                                processed_outputs = new_process_langgraph_output(k=k, v=v, session_id=st.session_state.session_id)
                                for content_dict in processed_outputs:  # Correct variable name used here
                                    if content_dict["type"] == "text":
                                        text_output = content_dict["content"]
                                        st.write(text_output)
                                        st.session_state.logger.info(text_output)
                                        output_history += text_output + "\n"
                                    elif content_dict["type"] == "visualization":
                                        fig = content_dict["content"]
                                        try:
                                            st.plotly_chart(fig)
                                        except Exception as e:
                                            st.error(f"An error occurred while plotting the figure: {e}. Please check the log file for more information.")
                                        # Store the figure in the session state and save the index
                                        fig_index = len(st.session_state.figures)
                                        st.session_state.figures.append(fig)

                        st.session_state.messages.append({"role": "assistant", "content": output_history, "image": fig_index, "url": "", "error":None})
                        time.sleep(0.5)

                except Exception as e:
                    error_message = f"An error occurred while processing your request: {e}. Please check more information in the log file, try again later or contact us for further investigation."
                    st.error(error_message)
                    st.session_state.logger.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": output_history, "image": fig_index, "url": "", "error": error_message})

                finally:
                    st.session_state.is_processing = False

            st.session_state["preselected_question"] = None
            st.rerun()

        # Allowing feedback 
        #if st.session_state.contributor_key == True:
        #    st.write("Please, feel free to provide a feedback: Was the answer helpful?")
        #    col1, col2, spacer = st.columns([0.5, 0.5, 12])
        #    with col1:
        #        positive_feedback = st.button("👍", key="pos_feedback")
        #    with col2:
        #        negative_feedback = st.button("👎", key="neg_feedback")
