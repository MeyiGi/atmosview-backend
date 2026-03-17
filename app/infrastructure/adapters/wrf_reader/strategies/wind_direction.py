from pathlib import Path
 
import numpy as np
import xarray as xr
 
from app.infrastructure.adapters.wrf_reader.variable_registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single 
 
from .base import VirtualVariableStrategy


@register_strategy("WIND_DIRECTION")
class WindDirectionStrategy(VirtualVariableStrategy):
    """Meteorological wind direction in degrees (0° = from North, clockwise)."""
 
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        u = read_single(ds, "U10", path)
        v = read_single(ds, "V10", path)
        return (270 - np.degrees(np.arctan2(v, u))) % 360