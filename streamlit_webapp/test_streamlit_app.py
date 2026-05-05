from streamlit.testing.v1 import AppTest

import app.core.memory.database_manager as database_manager
from streamlit_webapp import streamlit_utils


class DummyToolsDatabase:
    pass


def test_streamlit_app_renders_without_import_errors(monkeypatch):
    monkeypatch.setattr(streamlit_utils, "test_sparql_endpoint", lambda endpoint: False)
    monkeypatch.setattr(database_manager, "tools_database", lambda: DummyToolsDatabase())
    monkeypatch.setattr(database_manager, "memory_database", lambda: object())

    app = AppTest.from_file("streamlit_webapp/streamlit_app.py")
    app.run(timeout=30)

    assert not app.exception
    assert app.title
    assert app.title[0].value == "MetaboT - An AI-system for Metabolomics Data Exploration"
