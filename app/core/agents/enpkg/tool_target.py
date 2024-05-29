import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests



from langchain.pydantic_v1 import BaseModel, Field

from typing import Optional

from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)

from app.core.utils import setup_logger
from langchain.tools import BaseTool

logger = setup_logger(__name__)


class TargetInput(BaseModel):
    target_name: str = Field(
        description="A string containing the target representation."
    )


class TargetResolver(BaseTool):
    name: str = "TARGET_RESOLVER"
    description: str = """
    Convert a target_name string to ChEMBLTarget notation using the CHEMBL API.
    The function takes a target string as input and returns the ChEMBLTarget IRI.

    Args:
        target_name (str): A string containing the target_name representation.
    Returns:
        str: A string containing the ChEMBLTarget notation.
    """

    args_schema = TargetInput
    openai_key: str = None

    def __init__(self, openai_key: str = None):
        super().__init__()
        self.openai_key = openai_key

    def _run(
        self, target_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        url = "https://www.ebi.ac.uk/chembl/api/data/target"
        params = {"pref_name__contains": quote(target_name)}

        try:
            logger.debug(
                f"Requesting ChEMBL API from {url} with params {params} for {target_name}"
            )
            response = requests.get(url, params=params)

            if response.status_code == 200:
                # Parse the XML response
                root = ET.fromstring(response.content)

                # Assuming that the target_chembl_id is directly under the root
                # Adjust the path according to the actual structure of the XML
                chem_id = root.find(".//target_chembl_id")
                if chem_id is not None:
                    target_iri = f"https://www.ebi.ac.uk/chembl/target_report_card/{chem_id.text}"
                    logger.info(
                        "Found ChEMBLTarget IRI: %s for target name: %s",
                        target_iri,
                        target_name,
                    )
                    return f"{target_name} ChEMBLTarget IRI is {target_iri}"
                else:
                    logger.warning(
                        "No target found for %s, try again with a different name.",
                        target_name,
                    )
                    return f"No target found for {target_name}, try again with a different name."

            else:
                # Handle errors (e.g., invalid target name or server issue)
                logger.error("error response from ChEMBL API: %s", response.status_code)
                response.raise_for_status()

        except requests.RequestException as e:
            logger.exception("An error occurred while querying ChEMBL API: %s", str(e))
            return f"An error occurred: {str(e)}"
