import importlib
import os
import sys
import inspect
from uuid import uuid4

from ..utils import load_config
from ..session import setup_logger, create_user_session


logger = setup_logger(__name__)

config = load_config()


def create_all_agents(llms, graph, openai_key=None, session_id=None):
    """
    Dynamically create and initialize all agent modules as specified in the configuration.

    Parameters:
        llms (dict): A dictionary mapping LLM keys to their instances.
        graph: The graph instance used by the agents.
        openai_key (str, optional): The OpenAI API key to be used by agents. If not provided, it will be read from the environment.
        session_id (str, optional): A unique session identifier. If not provided, a new user session will be created.

    Returns:
        dict: A dictionary mapping agent names to their created executor instances.
    """
    
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
            module = importlib.import_module(module_path, package="MetaboT.app.core.agents")
            if hasattr(module, "create_agent"):
                # Inspect the create_agent function to determine parameter count
                func_signature = inspect.signature(module.create_agent)

                 # Filter the args_dict to only include parameters the function accepts
                filtered_args = {k: v for k, v in args_dict.items() if k in func_signature.parameters}

                # If the agent configuration specifies an LLM choice, pass that specific instance
                if "llm_instance" in func_signature.parameters:
                    if llms and "llm_choice" in agent:
                        if agent["llm_choice"] in llms:
                            filtered_args["llm_instance"] = llms[agent["llm_choice"]]
                        else:
                            logger.error(f"LLM '{agent['llm_choice']}' specified for agent '{agent['name']}' is not available in configuration. Falling back to default LLM 'llm_o'.")
                            filtered_args["llm_instance"] = llms.get("llm_o", None)
                    else:
                        filtered_args["llm_instance"] = llms.get("llm_o", None)
                # Execute each agent's create_agent function with the filtered args from the agent module
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
