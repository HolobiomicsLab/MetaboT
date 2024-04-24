import importlib
import os
import sys

from app.core.utils import load_config, setup_logger

logger = setup_logger(__name__)

config = load_config()


def create_all_agents(llms, graph):
    agents = config["agents"]
    executors = {}

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
                # Call the create_agent function
                executor = module.create_agent(llms, graph)
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
