from pathlib import Path
 
import numpy as np
import xarray as xr
 
from app.infrastructure.adapters.wrf_reader.registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single
 
from .base import VirtualVariableStrategy

@register_strategy("WIND_SPEED")
class WindSpeedStrategy(VirtualVariableStrategy):
    """Horizontal wind speed: sqrt(U10² + V10²)."""
 
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        u = read_single(ds, "U10", path)
        v = read_single(ds, "V10", path)
        return np.sqrt(u ** 2 + v ** 2)