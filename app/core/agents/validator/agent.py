import os

from langchain.agents import AgentExecutor, create_openai_tools_agent

from app.core.utils import get_module_prefix, import_tools
from app.core.session import setup_logger

from .prompt import CHAT_PROMPT, MODEL_CHOICE


logger = setup_logger(__name__)


def create_agent(llms, graph, llm_instance=None) -> AgentExecutor:
    
    logger.info("Creating agent with tools...")
    directory = os.path.dirname(__file__)
    module_prefix = get_module_prefix(__name__)

    tools = import_tools(directory, module_prefix)

    try:
        model_to_use = llm_instance if llm_instance is not None else llms[MODEL_CHOICE]
        agent = create_openai_tools_agent(model_to_use, tools, CHAT_PROMPT)
        executor = AgentExecutor(agent=agent, tools=tools)
        logger.info(f"Agent created successfully with {len(tools)} tools.")
        return executor
    except Exception as e:
        logger.error("Failed to create agent", exc_info=True)
        raise
