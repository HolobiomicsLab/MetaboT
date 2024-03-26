import requests
from pathlib import Path
import logging.config

parent_dir = Path(__file__).parent.parent
config_path = parent_dir / "config" / "logging.ini"
logging.config.fileConfig(config_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def smiles_to_inchikey(smiles: str) -> str:
    """
    Convert a SMILES string to InChIKey notation using the GNPS API.

    Args:
        smiles (str): A string containing the SMILES representation of a molecule.
    Returns:
        str: A string containing the InChIKey notation of the molecule.

    Example usage:
    smiles_string = "CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45"
    inchikey = smiles_to_inchikey(smiles_string)

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
