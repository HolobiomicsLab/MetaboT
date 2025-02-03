from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

PROMPT = """Your only purpose is to call SAY_HELLO_TOOL with input to the tool is a string 'say hello please'. 
Ignore all other messages. Provide the output of the tool to the supervisor without modification, including hastags and question marks. """

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            PROMPT,
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


MODEL_CHOICE = "hugface_Llama_3_3_70B"
