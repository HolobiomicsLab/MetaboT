import requests


def smiles_to_inchikey(smiles : str):
    """
    Convert a SMILES string to InChIKey notation using the GNPS API.

    :param smiles: A string containing the SMILES representation of a molecule.
    :return: A string containing the InChIKey notation of the molecule.
    """
    url = "https://structure.gnps2.org/inchikey"
    # # https://ccms-ucsd.github.io/GNPSDocumentation/api/#structure-conversion
    params = {'smiles': smiles}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return "InChIKey is "+response.text
    else:
        # Handle errors (e.g., invalid SMILES string or server issue)
        response.raise_for_status()

    # Example usage
    # smiles_string = "CCC12CCCN3C1C4(CC3)C(CC2)NC5=CC=CC=C45" 
    # inchikey = smiles_to_inchikey(smiles_string)

