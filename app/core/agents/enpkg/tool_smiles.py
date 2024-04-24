import logging.config
from pathlib import Path

import requests
from langchain_core.tools import tool

from app.core.utils import setup_logger

from ..tool_interface import ToolTemplate

logger = setup_logger(__name__)


class SMILESResolver(ToolTemplate):

    def __init__(self):
        super().__init__()

    @tool("SMILES_RESOLVER")
    def tool_func(smiles: str) -> str:
        """
        Convert a SMILES string to InChIKey notation using the GNPS API.
        The function takes a SMILES string as input and returns the InChIKey notation of the molecule.

        Args:
            smiles (str): A string containing the SMILES representation of a molecule.
        Returns:
            str: A string containing the InChIKey notation of the molecule.

        Example usage:
        smiles_string = "CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45"
        inchikey = tool_func(smiles_string)

        """
        url = "https://structure.gnps2.org/inchikey"
        params = {"smiles": smiles}
        logger.info("Requesting InChIKey from GNPS API with params %s", params)
        response = requests.get(url, params=params)

        if response.status_code == 200:
            logger.info("InChIKey response: %s", response.text)
            return "InChIKey is " + response.text
        else:
            logger.error("error response from GNPS API: %s", response.status_code)
            response.raise_for_status()
