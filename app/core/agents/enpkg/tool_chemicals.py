from __future__ import annotations


from pathlib import Path

from typing import List, Optional

from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from langchain_core.documents import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)

from app.core.session import setup_logger

import os

logger = setup_logger(__name__)


class ChemicalInput(BaseModel):
    chemical_name: str = Field(description="natural product compound string")


class ChemicalResolver(BaseTool):
    name: str = "CHEMICAL_RESOLVER"
    description: str = """
    Resolves chemicals to NPC Class URIs using a specific CSV database.
    
    Args:
        chemical_name str: the chemical name string.
    
    Returns:
        Dict[str, str]: a dictionary that contains the output chemical name and corresponding NPC Class URI.
    """

    args_schema = ChemicalInput
    csv_data: List[Document] = None
    retriever: Any = None
    openai_key: str = None

    def __init__(self, openai_key: str = None):
        super().__init__()
        self.openai_key = openai_key

    def _run(
            self,
            chemical_name: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        logger.info("Using NPC Classifier for chemical resolution.")

        # Verify that csv_data and retriever are initialized
        if not self.csv_data or not self.retriever:
            self.csv_data = self.csv_loader()
            self.retriever = self.npc_retriever(self.csv_data)

        # Retrieve the NPC Class URI(s) related to the chemical name
        uris = self.retriever.invoke(chemical_name)[0].page_content
        res = f"{chemical_name}, NPCCLass, {uris}"
        logger.info(f"NPC Classifier result: {res}")
        return res

    def csv_loader(self):
        """
        loads a CSV file with specified delimiter and fieldnames from a given file
        path.

        Returns:
            Any: a dictionary that contains the data from the CSV file.
        """

        dir_path = Path(__file__).resolve().parent.parent.parent.parent
        file_path = dir_path / "data" / "npc_all.csv"

        loader = CSVLoader(
            file_path=file_path,
            csv_args={
                "delimiter": ",",
                "fieldnames": ["NPCClass", "NPCPathway", "NPCSuperClass"],
            },
        )
        return loader.load()

    def npc_retriever(self, data):
        """
        Processes input data, splits it into chunks, generates embeddings,
        creates a FAISS database, and returns a retriever object for searching.

        Args:
            data: a dictionary containing the data to be processed.

        Returns:
            Any: a retriever object for searching.
        """
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        # chunk_size=1000 amounts to ~6 lignes in file npc_all.csv
        texts = text_splitter.split_documents(data)
        embeddings = OpenAIEmbeddings(api_key=self.openai_key)
        db = FAISS.from_documents(texts, embeddings)

        return db.as_retriever()

