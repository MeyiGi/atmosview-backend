from typing_extensions import Protocol
from pathlib import Path

import numpy as np
import xarray as xr

class VirtualVariableStrategy(Protocol):
    """Strategy interface for reading WRF files"""
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray: ...