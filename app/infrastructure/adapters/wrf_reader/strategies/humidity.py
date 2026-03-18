from pathlib import Path
 
import numpy as np
import xarray as xr
 
from app.infrastructure.adapters.wrf_reader.registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single
 
from .base import VirtualVariableStrategy
 
 
@register_strategy("HUMIDITY")
class HumidityStrategy(VirtualVariableStrategy):
    """2-metre specific humidity (Q2) in kg/kg."""
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        return read_single(ds, "Q2", path)