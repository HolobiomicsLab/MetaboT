import importlib
import os
import sys
import inspect
from uuid import uuid4

from app.core.utils import load_config, setup_logger, create_user_session

logger = setup_logger(__name__)

config = load_config()


def create_all_agents(llms, graph, openai_key = None, session_id = None):
    agents = config["agents"]
    executors = {}

    if session_id is None:
        session_id = create_user_session()

    if openai_key is None:
        openai_key = os.getenv("OPENAI_API_KEY")

    args_dict = {
            'llms': llms,
            'graph': graph,
            'openai_key': openai_key,
            'session_id': session_id
        }

    for agent in agents:
        module_path = agent["path"]
        agent_dir = os.path.dirname(module_path.replace(".", "/"))

        # Ensure the directory is in sys.path for relative imports within the module
        if agent_dir not in sys.path:
            sys.path.append(agent_dir)

        try:
            # Import the agent creation module dynamically
            module = importlib.import_module(module_path)
            if hasattr(module, "create_agent"):
                # Inspect the create_agent function to determine parameter count
                func_signature = inspect.signature(module.create_agent)

                 # Filter the args_dict to only include parameters the function accepts
                filtered_args = {k: v for k, v in args_dict.items() if k in func_signature.parameters}

                # Execute each agent's create_agent function with the filtered args from the own module
                executor = module.create_agent(**filtered_args)

                executors[agent["name"]] = executor
                
            else:
                logger.info(
                    f"Module {module_path} does not have a 'create_agent' function."
                )
        except Exception as e:
            logger.error(f"Failed to import or create agent for '{agent['name']}': {e}")

    logger.info(f"Created {len(executors)} agents.")
    logger.info(f"Agents: {list(executors.keys())}")
    return executors
