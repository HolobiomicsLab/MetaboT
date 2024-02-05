from prompts import default_prompt

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
from typing import List, Optional
from langchain.callbacks import StreamlitCallbackHandler


def run_agent(
    question: str,
    tools: List,
    st_callback: Optional[StreamlitCallbackHandler] = None,
    verbose: bool = True
) -> str:
    """
    Executes an agent to answer a question using a set of tools, with optional Streamlit integration.

    This function takes a question as input and runs it through an agent that uses a set of provided LangChain Tool instances.
    It can optionally use a Streamlit callback for integration with Streamlit applications.

    Args:
        question (str): The question or input string for the agent to process.
        tools (List[LangChain Tool]): A list of LangChain Tool instances for the agent to use in processing the question.
        st_callback (StreamlitCallbackHandler, optional): An instance for Streamlit callback integration. Defaults to None.
        verbose (bool, optional): If True, prints the question to the console. Defaults to True.

    Returns:
        str: The agent's response after processing the question with the given tools.

    """
    temperature = 0.3
    model = "gpt-4"
    verbose_llm = True
    agent_type = AgentType.OPENAI_FUNCTIONS

    if verbose:
        print(question)

    llm = ChatOpenAI(temperature=temperature, model=model, verbose=verbose_llm)
    agent = initialize_agent(
        tools, llm, prompt=default_prompt, agent=agent_type, verbose=verbose)

    formatted_prompt = default_prompt.format(question=question)
    response = agent.run(formatted_prompt, callbacks=[
                         st_callback] if st_callback is not None else [])

    return response
