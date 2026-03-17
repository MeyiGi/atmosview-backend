from pathlib import Path

import numpy as np
import xarray as xr

from app.infrastructure.adapters.wrf_reader.registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single

from .base import VirtualVariableStrategy

@register_strategy("TEMPERATURE")
class TemperatureStrategy(VirtualVariableStrategy):
    """2-metre air temperature in Kelvin (T2)."""
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        return read_single(ds, "T2", path)