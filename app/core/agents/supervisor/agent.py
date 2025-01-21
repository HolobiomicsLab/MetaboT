from langchain.agents import AgentExecutor
from langchain_core.language_models import BaseChatModel 
# langchain output parser for OpenAI functions
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .prompt import MODEL_CHOICE, PROMPT

from app.core.utils import load_config, setup_logger

logger = setup_logger(__name__)

config = load_config()


def create_agent(llms, graph) -> AgentExecutor:
    """Configure and return a supervisor agent with decision-making logic for task routing."""

    llm:BaseChatModel = llms[MODEL_CHOICE]
    members = config["supervisor"]["members"]
    options = ["FINISH"] + members

    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
            },
            "required": ["next"],
        },
    }

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    return (
        prompt
        # | llm.bind_functions(functions=[function_def], function_call="route")
        | llm.bind(functions=[function_def], function_call="auto")
        | JsonOutputFunctionsParser()
    )