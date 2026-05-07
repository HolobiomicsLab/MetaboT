from app.core.agents.sparql import agent as sparql_agent
from app.core.agents.sparql import tool_sparql


def _construct_tool(**kwargs):
    return tool_sparql.GraphSparqlQAChain.model_construct(**kwargs)


def test_create_agent_passes_openai_key_to_import_tools(monkeypatch):
    captured = {}

    def fake_import_tools(directory, module_prefix, **kwargs):
        captured["tool_kwargs"] = kwargs
        return ["tool"]

    def fake_create_openai_tools_agent(model, tools, prompt):
        captured["agent_model"] = model
        captured["agent_tools"] = tools
        return "agent"

    def fake_agent_executor(agent, tools):
        captured["executor_agent"] = agent
        captured["executor_tools"] = tools
        return "executor"

    monkeypatch.setattr(sparql_agent, "import_tools", fake_import_tools)
    monkeypatch.setattr(
        sparql_agent,
        "create_openai_tools_agent",
        fake_create_openai_tools_agent,
    )
    monkeypatch.setattr(sparql_agent, "AgentExecutor", fake_agent_executor)

    executor = sparql_agent.create_agent(
        llms={sparql_agent.MODEL_CHOICE: "model"},
        graph="graph",
        session_id="session-123",
        openai_key="cli-key",
    )

    assert executor == "executor"
    assert captured["tool_kwargs"] == {
        "graph": "graph",
        "llm": {sparql_agent.MODEL_CHOICE: "model"},
        "session_id": "session-123",
        "openai_key": "cli-key",
    }
    assert captured["agent_model"] == "model"
    assert captured["executor_agent"] == "agent"
    assert captured["executor_tools"] == ["tool"]


def test_search_nodes_uses_explicit_openai_key(monkeypatch):
    captured = {}

    class FakeEmbeddings:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key

    class FakeVectorStore:
        def similarity_search(self, query, limit):
            captured["query"] = query
            captured["limit"] = limit
            return ["related-node"]

    def fake_load_local(path, embeddings, allow_dangerous_deserialization=False):
        captured["db_path"] = path
        captured["embeddings"] = embeddings
        captured["allow_dangerous_deserialization"] = allow_dangerous_deserialization
        return FakeVectorStore()

    monkeypatch.setattr(tool_sparql, "OpenAIEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(tool_sparql.FAISS, "load_local", fake_load_local)

    tool = _construct_tool(openai_key="cli-key")
    result = tool.search_nodes("SELECT * WHERE { ?s ?p ?o }")

    assert captured["api_key"] == "cli-key"
    assert captured["query"] == "SELECT * WHERE { ?s ?p ?o }"
    assert captured["limit"] == 12
    assert captured["allow_dangerous_deserialization"] is True
    assert result == ["related-node"]


def test_search_nodes_falls_back_to_env_openai_key(monkeypatch):
    captured = {}

    class FakeLLMChain:
        def __init__(self, llm, prompt):
            self.llm = llm
            self.prompt = prompt

    class FakeEmbeddings:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key

    class FakeVectorStore:
        def similarity_search(self, query, limit):
            captured["query"] = query
            captured["limit"] = limit
            return ["related-node"]

    def fake_load_local(path, embeddings, allow_dangerous_deserialization=False):
        captured["db_path"] = path
        captured["embeddings"] = embeddings
        captured["allow_dangerous_deserialization"] = allow_dangerous_deserialization
        return FakeVectorStore()

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setattr(tool_sparql, "LLMChain", FakeLLMChain)
    monkeypatch.setattr(tool_sparql, "OpenAIEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(tool_sparql.FAISS, "load_local", fake_load_local)

    tool = tool_sparql.GraphSparqlQAChain(
        llm={"llm_o": object(), "llm_mini": object()},
        graph=object(),
        session_id="session-123",
        openai_key=None,
    )
    result = tool.search_nodes("SELECT * WHERE { ?s ?p ?o }")

    assert captured["api_key"] == "env-key"
    assert captured["query"] == "SELECT * WHERE { ?s ?p ?o }"
    assert captured["limit"] == 12
    assert captured["allow_dangerous_deserialization"] is True
    assert result == ["related-node"]
