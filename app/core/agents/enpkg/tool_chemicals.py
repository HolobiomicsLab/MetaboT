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
    Resolves chemicals to InChi keys.
    Try to fetch the chemical InCHikey from National cancer institute API, if none, fallback to the NPCClass retriever,
    which is a specific database correspondence between chemical names and NPC class URIs from ENPKG.

    Args:
        chemical_name str : the chemical name string.

    Returns:
        Dict[str, str]: a dictionary that contains the output chemical name and corresponding URI.
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

        inchi_key = self.CIRconvert(chemical_name)

        if inchi_key:
            return f"{chemical_name}, InChIKey, {inchi_key}"

        logger.info("InChIKey not found, trying NPC Classifier")
        ## verify that csv_data is in the attributes of the class
        if not self.csv_data or not self.retriever:
            self.csv_data = self.csv_loader()
            self.retriever = self.npc_retriever(self.csv_data)

        uris = self.retriever.invoke(chemical_name)[0].page_content
        # if bug, try directly get_relevant_documents(),
        # https://api.python.langchain.com/en/latest/vectorstores/langchain_core.vectorstores.VectorStoreRetriever.html#langchain_core.vectorstores.VectorStoreRetriever
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

    # Chemical name to Standard InChIKey
    def CIRconvert(self, ids):
        """
        Takes a chemical compound identifier, queries a specific URL to retrieve
        its InChIKey, and returns the compound identifier along with the corresponding InChIKey.

        Args:
            ids: a string that represents a chemical compound identifier.
        Returns:
            str: a string that contains the chemical compound identifier along with the corresponding InChIKey.
        Raises:
            HTTPError: An error occurred while querying the server.
            URLError: An error occurred while querying the URL.
            Exception: An unexpected error occurred.
        """
        try:
            # TODO [Franck]: MIME type should be set to "text/plain" explicitely, see https://cactus.nci.nih.gov/chemical/structure/stdinchikey
            url = (
                "http://cactus.nci.nih.gov/chemical/structure/"
                + quote(ids)
                + "/stdinchikey"
            )
            ans = urlopen(url).read().decode("utf8")
            logger.info(f"Found InChIKey: {ans} for {ids}")
            return ": ".join([ids, ans])

        except HTTPError as e:
            logger.error("HTTPError occurred: %s %s", e.code, e.reason)
        except URLError as e:
            logger.error("URLError occurred: %s", e.reason)
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
        return None
