from pathlib import Path

import xarray as xr
import numpy as np

from app.domain.exceptions import VariableNotFoundError
from app.infrastructure.adapters.wrf_reader.helpers import read_single
from app.infrastructure.adapters.wrf_reader.registry import register_strategy

from .base import VirtualVariableStrategy

@register_strategy("PRECIPITATION")
class PrecipitationStrategy(VirtualVariableStrategy):
    """Total precipitation = RAINC + RAINNC (convective + non-convective)."""
    _FIELDS = ("RAINC", "RAINNC")

    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        fields = [f for f in self._FIELDS if f in ds]
        if not fields:
            raise VariableNotFoundError(
                f"None of {self._FIELDS} found in '{path.name}'"
                f"Available: {list(ds.data_vars)}"
            )
        
        return np.add.reduce([read_single(ds, field, path) for field in fields])
