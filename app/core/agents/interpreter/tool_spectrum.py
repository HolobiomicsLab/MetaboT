from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

import os
import matplotlib

matplotlib.use("Agg")


# Define the input schema for the SpectrumPlotter tool.
class SpectrumPlotInput(BaseModel):
    usi: str = Field(description="Universal Spectrum Identifier for the spectrum.")
    precursor_mz: float = Field(description="The precursor m/z value.")
    precursor_charge: Optional[int] = Field(default=0, description="The precursor charge. Default is 0.")


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

    def _run(
            self,
            usi: str,
            precursor_mz: float,
            precursor_charge: Optional[int] = 0,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        # Import required libraries for spectrum processing and plotting.
        import matplotlib.pyplot as plt
        import spectrum_utils.plot as sup
        import spectrum_utils.spectrum as sus

        # Retrieve the spectrum using the provided USI.
        spectrum = sus.MsmsSpectrum.from_usi(
            usi, precursor_mz=precursor_mz, precursor_charge=precursor_charge
        )

        # Process the spectrum.
        fragment_tol_mass, fragment_tol_mode = 10, "ppm"
        spectrum = spectrum.set_mz_range(min_mz=100, max_mz=1400)
        # Additional processing steps (e.g., removing peaks) can be added here if needed.

        # Plot the spectrum.
        fig, ax = plt.subplots(figsize=(12, 6))
        sup.spectrum(spectrum, grid=False, ax=ax)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        # Save the plot to a file.
        output_path = "spectrum_plot_2.png"
        plt.savefig(output_path, bbox_inches="tight", dpi=300, transparent=True)
        plt.show()
        plt.close()

        # Return a message including the location of the saved plot.
        return {"result": f"Spectrum plot saved to {output_path}"}


