import requests

from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)


from app.core.utils import setup_logger


logger = setup_logger(__name__)


class SMILESInput(BaseModel):
    smiles: str = Field(
        description="A string containing the SMILES representation of a molecule."
    )


class SMILESResolver(BaseTool):
    name: str = "SMILES_RESOLVER"
    description: str = """
    Convert a SMILES string to InChIKey notation using the GNPS API.
    The function takes a SMILES string as input and returns the InChIKey notation of the molecule.

    Args:
        smiles (str): A string containing the SMILES representation of a molecule.
    Returns:
        str: A string containing the InChIKey notation of the molecule.

    Example usage:
    smiles_string = "CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45"
    inchikey = _run(smiles_string)
    """
    args_schema = SMILESInput
    openai_key: str = None

    def __init__(self, openai_key: str = None):
        super().__init__()
        self.openai_key = openai_key

    def _run(
        self, smiles: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:

        url = "https://structure.gnps2.org/inchikey"
        params = {"smiles": smiles}
        logger.info("Requesting InChIKey from GNPS API with params %s", params)
        response = requests.get(url, params=params)

        if response.status_code == 200:
            logger.info("InChIKey response: %s", response.text)
            return {"SMILES": smiles, "InChIKey": response.text}
        else:
            logger.error("error response from GNPS API: %s", response.status_code)
            response.raise_for_status()
