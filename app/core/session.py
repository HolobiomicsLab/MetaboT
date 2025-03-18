#Mainly used to integrate to web applications, this snippet is used to create a session context for the user and the thread. This is useful for logging and debugging purposes, as it allows you to track the user's session and the thread that is currently running. This snippet also includes a function to set up a logger that logs to a file and the console. The logger is set up to log to a file in the temporary directory of the system, with a separate log file for each user session. The logger also logs to the console for real-time debugging. The session context and thread context are stored using Python's ContextVar, which allows you to store and retrieve values within a context, such as a session or a thread.

from contextvars import ContextVar
from pathlib import Path
import logging
import logging.config
import tempfile
from uuid import uuid4
from datetime import date
import sys

session_id_context = ContextVar('session_id', default=None)
thread_id_context = ContextVar('thread_id', default=None)

def initialize_session_context(session_id):
    session_id_context.set(session_id)
    print(f"Session ID set to: {session_id}")


def create_user_session(session_id=None, user_session_dir=False, input_dir=False):
    """
    If no session_id is provided, creates a new session_id and all the temporary directory for the metabot to save generated and input files.
    If session_id is provided, returns the path to the temporary directory for the metabot depending on the provided argument.

    Args:
        session_id (str, optional): The session_id to use. Defaults to None.
        user_session_dir (bool, optional): If True, returns the path to the temporary directory for the metabot. Defaults to False.
        input_dir (bool, optional): If True, returns the path to the input files directory for the metabot. Defaults to False.

    Returns:
        str: The session_id if no session_id is provided.
        Path: The path to the temporary directory for the metabot if user_session_dir is True.
        Path: The path to the input files directory for the metabot if input_dir is True.
    """

    if session_id is None:
        session_id = str(uuid4().hex)

        # Create a temporary directory for the metabot
        metabot_temp_dir = Path(tempfile.gettempdir()) / "metabot"
        metabot_temp_dir.mkdir(parents=True, exist_ok=True)

        user_session_dir = metabot_temp_dir / session_id
        user_session_dir.mkdir(parents=True, exist_ok=True)

        input_dir = user_session_dir / "input_files"
        input_dir.mkdir(parents=True, exist_ok=True)

        return session_id
    
    else:
        if user_session_dir:
            user_session_dir = Path(tempfile.gettempdir()) / "metabot" / session_id
            return user_session_dir
        
        if input_dir:
            input_dir = Path(tempfile.gettempdir()) / "metabot" / session_id / "input_files"
            return input_dir
        

def setup_logger(name):
    """
    Set up logging configuration dynamically based entirely on code.

    Parameters:
    - name (str): Typically __name__ from the calling module.

    Returns:
    - logger (logging.Logger): Configured logger object.
    """

    try:
        # Retrieve the session ID
        session_id = session_id_context.get()  # Always retrieve the session ID safely

        # Create a logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)  # Set the default logging level

        # Formatter definition for file handler
        detailed_formatter = logging.Formatter('%(asctime)s - %(name)s- %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

        # Formatter for console handler
        simple_formatter = logging.Formatter('%(name)s %(levelname)s - %(message)s')

        # Remove existing handlers to prevent duplicate logs
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
        logger.propagate = False  # Prevent the logger from propagating messages to the root logger

        # Log file path setup
        if session_id:
            log_file_path = Path(tempfile.gettempdir()) / "metabot" / session_id / "metabot.log"
        else:
            parent_dir = Path(__file__).resolve().parent.parent
            log_file_path = parent_dir / "config" / "logs" / "app.log"

        # Ensure directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # File handler setup
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            mode='a',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        # Console handler setup
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

        return logger
    
    except Exception as e:
        
        print(f"An error occurred: {e}")
        return None

def get_session_id():
    session_id = session_id_context.get()
    print(f"Session ID retrieved: {session_id}")
    return session_id

def initialize_thread_id(thread_id):
    thread_id_context.set(thread_id)
    print(f"Thread ID set to: {thread_id}")

def get_thread_id():
    thread_id = thread_id_context.get()
    print(f"Thread ID retrieved: {thread_id}")
    return thread_id
