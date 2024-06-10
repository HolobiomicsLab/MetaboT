
import pandas as pd

import logging
from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
from langchain.pydantic_v1 import BaseModel, Field

from typing import Optional


from app.core.agents.sparql.base import KgbotBaseTool
from app.core.utils import setup_logger


logger = setup_logger(__name__)

class PlantInput(BaseModel):
    plant_name: str = Field(
        description="A string containing the plant name to search for in the database."
    )


class PlantDatabaseChecker(KgbotBaseTool):
    name: str = "PLANT_DATABASE_CHECKER"
    description: str = """
    Check if a plant name is present in the database.

    Args:
        plant_name (str): A string containing the plant name to search for.
    Returns:
        str: A string indicating whether the plant is present in the database or not.
    """
    requires_params = False  # This tool does not require additional initialization parameters

    args_schema = PlantInput

    def __init__(self):
        super().__init__()

    def _run(
            self, plant_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        csv_path = '/Users/madinabekbergenova/Desktop/LLMs/kgbot_dev_new/app/data/submitted_plants.csv'

        try:
            # Load the CSV file into a pandas DataFrame
            df = pd.read_csv(csv_path)

            # Check if the plant name is in the DataFrame
            if plant_name in df['submittedTaxon'].values:
                logger.info(f"The plant {plant_name} is present in the database.")
                return f"The plant {plant_name} is present in the database."
            else:
                logger.info(f"The plant {plant_name} is not present in the database.")
                return f"The plant {plant_name} is not present in the database."
        except Exception as e:
            logger.exception(f"An error occurred while checking the plant database: {str(e)}")
            return f"An error occurred: {str(e)}"


