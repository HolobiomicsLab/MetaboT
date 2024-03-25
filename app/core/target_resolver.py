import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote


def target_name_to_target_id(target_name: str):
    """
    Convert a target_name string to ChEMBLTarget notation using the CHEMBL API.

    Args:
        target_name (str): A string containing the target_name representation.
    Returns:
        str: A string containing the ChEMBLTarget notation.
    """
    url = "https://www.ebi.ac.uk/chembl/api/data/target"
    params = {"pref_name__contains": quote(target_name)}

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Parse the XML response
            root = ET.fromstring(response.content)

            # Assuming that the target_chembl_id is directly under the root
            # Adjust the path according to the actual structure of the XML
            chem_id = root.find(".//target_chembl_id")
            if chem_id is not None:
                return {
                    target_name
                    + "ChEMBLTarget IRI is https://www.ebi.ac.uk/chembl/target_report_card/"
                    + chem_id.text
                }
            else:
                return f"No target found for {target_name}, try again with a different name."

        else:
            # Handle errors (e.g., invalid target name or server issue)
            response.raise_for_status()

    except requests.RequestException as e:
        return f"An error occurred: {str(e)}"
