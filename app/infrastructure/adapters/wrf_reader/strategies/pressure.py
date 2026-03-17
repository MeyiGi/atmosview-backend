from pathlib import Path

import numpy as np
import xarray as xr

from app.infrastructure.adapters.wrf_reader.variable_registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single

from .base import VirtualVariableStrategy

@register_strategy("PRESSURE")
class PressureStrategy(VirtualVariableStrategy):
    """Surface pressure in Pascals (PSFC)."""
    def compute(ds: xr.Dataset, path: Path) -> np.ndarray:
        return read_single(ds, "PSFC",path)