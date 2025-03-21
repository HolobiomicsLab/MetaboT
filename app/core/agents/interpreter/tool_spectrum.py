from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
import tkinter as tk
from ...memory.database_manager import tools_database
import pandas as pd
import json
import os
import matplotlib
import requests


matplotlib.use("Agg")
from app.core.session import setup_logger, create_user_session
logger = setup_logger(__name__)

# Define the input schema for the SpectrumPlotter tool.
class SpectrumPlotInput(BaseModel):
    input_data: Union[str, Dict[str, Any]] = Field(
        description="Either a dictionary with USI and precursor_mz or a file path to a CSV file containing these values."
    )
    precursor_charge: Optional[int] = Field(default=0, description="The precursor charge. Default is 0.")
    # usi: str = Field(description="Universal Spectrum Identifier for the spectrum.")
    # precursor_mz: float = Field(description="The precursor m/z value.")
    # precursor_charge: Optional[int] = Field(default=0, description="The precursor charge. Default is 0.")


# Define the SpectrumPlotter tool.
class SpectrumPlotter(BaseTool):
    name: str = "SPECTRUM_PLOTTER"
    description: str = """
    Plots a spectrum given its USI, precursor m/z, and precursor charge.

    Args:
        usi (str): The Universal Spectrum Identifier.
        precursor_mz (float): The precursor m/z value.
        precursor_charge (int, optional): The precursor charge. Default is 0.

    Returns:
        A message indicating where the spectrum plot has been saved.
    """
    args_schema = SpectrumPlotInput
    session_id: str = None
    openai_key: str = None

    def __init__(self, openai_key: str, session_id: str):
        super().__init__()
        self.openai_key = openai_key
        self.session_id = session_id
    # version 2
    def _run(
            self,
            input_data: Union[str, Dict[str, Any]] = None,
            usi: Optional[str] = None,
            precursor_mz: Optional[float] = None,
            precursor_charge: Optional[int] = 0,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        import matplotlib.pyplot as plt
        import spectrum_utils.plot as sup
        import spectrum_utils.spectrum as sus
        session_dir = create_user_session(self.session_id, user_session_dir=True)
        db_manager = tools_database()
        os.makedirs(session_dir, exist_ok=True)

        output_path = os.path.join(session_dir, "spectrum_plot.png")
        # If input_data is provided, it should be used instead of the other parameters
        if input_data:
            if isinstance(input_data, str) and input_data.endswith(".csv"):
                # Read CSV and extract the first row of required columns
                df = pd.read_csv(input_data)

                # Check required columns
                if not {'usi', 'parent_mass'}.issubset(df.columns):
                    return {"error": "CSV file must contain 'usi' and 'parent_mass' columns."}

                first_row = df.iloc[0]
                usi = first_row['usi']
                precursor_mz = first_row['parent_mass']
            elif isinstance(input_data, dict) and 'usi' in input_data and 'precursor_mz' in input_data:
                usi = input_data['usi']
                precursor_mz = input_data['precursor_mz']
            else:
                return {
                    "error": "Invalid input. Provide a dictionary with 'usi' and 'precursor_mz' or a valid CSV file path."}

        if not usi or not precursor_mz:
            return {"error": "Both 'usi' and 'precursor_mz' are required."}
        # Retrieve the spectrum using the provided USI and precursor_mz
        # spectrum = sus.MsmsSpectrum.from_usi(
        #         usi, precursor_mz=precursor_mz, precursor_charge=precursor_charge
        #     )
        # Process the spectrum
        # spectrum = spectrum.set_mz_range(min_mz=100, max_mz=1400)
        # plt.ion()
        #
        # # Plot the spectrum
        # fig, ax = plt.subplots(figsize=(12, 6))
        # sup.spectrum(spectrum, grid=False, ax=ax)
        # ax.spines["right"].set_visible(False)
        # ax.spines["top"].set_visible(False)
            # Construct the GNPS URL
        url = f"https://metabolomics-usi.gnps2.org/png/?usi1={usi}"
        # output_path = f"{session_dir}/spectrum_plot.png"
        try:
                # Send request to GNPS
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for bad status codes

                # Save the PNG image
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"Spectrum PNG saved as {output_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch spectrum PNG: {e}")


        # Save the plot to a file
        # output_path = f"{session_dir}/spectrum_plot.png"
        # plt.savefig(output_path, bbox_inches="tight", dpi=300, transparent=True)



        output_data = {"output": {"paths": output_path}}

        try:
            db_manager.put(data=json.dumps(output_data), tool_name="tool_spectrum")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

        return {"result": f"Spectrum plot saved to {output_path}"}

    # first version
    # def _run(
    #         self,
    #         usi: str,
    #         precursor_mz: float,
    #         precursor_charge: Optional[int] = 0,
    #         run_manager: Optional[CallbackManagerForToolRun] = None,
    # ) -> Dict[str, Any]:
    #     # Import required libraries for spectrum processing and plotting.
    #     import matplotlib.pyplot as plt
    #     import spectrum_utils.plot as sup
    #     import spectrum_utils.spectrum as sus
    #
    #     # Retrieve the spectrum using the provided USI.
    #     spectrum = sus.MsmsSpectrum.from_usi(
    #         usi, precursor_mz=precursor_mz, precursor_charge=precursor_charge
    #     )
    #
    #     # Process the spectrum.
    #     fragment_tol_mass, fragment_tol_mode = 10, "ppm"
    #     spectrum = spectrum.set_mz_range(min_mz=100, max_mz=1400)
    #     # Additional processing steps (e.g., removing peaks) can be added here if needed.
    #     plt.ion()
    #     # Plot the spectrum.
    #     fig, ax = plt.subplots(figsize=(12, 6))
    #     sup.spectrum(spectrum, grid=False, ax=ax)
    #     ax.spines["right"].set_visible(False)
    #     ax.spines["top"].set_visible(False)
    #
    #     plt.show(block=True)
    #     # Save the plot to a file.
    #     output_path = "spectrum_plot_2.png"
    #
    #     plt.savefig(output_path, bbox_inches="tight", dpi=300, transparent=True)
    #
    #     plt.close()
    #
    #     db_manager = tools_database()
    #
    #     output_data = {
    #         "output": {
    #             "paths": output_path
    #         }
    #     }
    #
    #     try:
    #         db_manager.put(data=json.dumps(output_data), tool_name="tool_spectrum")
    #     except Exception as e:
    #         logger.error(f"Error saving to database: {e}")
    #
    #     # Return a message including the location of the saved plot.
    #     return {"result": f"Spectrum plot saved to {output_path}"}
    #

# input_usi = "mzspec:MSV000087728:VGF155_D05_features_ms2_neg.mgf:scan:6"
# input_precursor_mz = 425.1241760253906
#
# if __name__ == "__main__":
#     plotter = SpectrumPlotter(session_id="123",openai_key="123")
#     result = plotter._run( usi='mzspec:MSV000087728:VGF155_D05_features_ms2_neg.mgf:scan:29', precursor_mz=425.1241760253906)
#
#     print(result)
# input_path="/var/folders/20/4kgcw5656h12ss_nj18mndwm0000gn/T/metabot/2a8b5852a90c4e43998a454da115338b/tmpccevhc87.csv"
# if __name__ == "__main__":
#     plotter = SpectrumPlotter()
#     result = plotter._run(
#         input_data=input_path
#     )
#     print(result)