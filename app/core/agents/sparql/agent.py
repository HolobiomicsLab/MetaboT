import os

from langchain.agents import AgentExecutor, create_openai_tools_agent

from app.core.utils import get_module_prefix, import_tools
from app.core.session import setup_logger


from .prompt import CHAT_PROMPT, MODEL_CHOICE

logger = setup_logger(__name__)


def create_agent(llms, graph, session_id) -> AgentExecutor:
    logger.info("Creating agent with tools...")
    directory = os.path.dirname(__file__)
    module_prefix = get_module_prefix(__name__)

    tool_parameters = {
        "graph": graph,
        "llm": llms,
        "session_id": session_id
    }

    tools = import_tools(directory, module_prefix, **tool_parameters)

    try:
        agent = create_openai_tools_agent(llms[MODEL_CHOICE], tools, CHAT_PROMPT)
        executor = AgentExecutor(agent=agent, tools=tools)
        logger.info(f"Agent created successfully with {(tools)} tools.")
        return executor
    except Exception as e:
        logger.error("Failed to create agent", exc_info=True)
        raise
