from pathlib import Path
from typing import Callable, Protocol, Type

import numpy as np
import xarray as xr

class VirtualVariableStrategy(Protocol):
    """Strategy interface for reading WRF files"""
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray: ...


_REGISTRY: dict[str, VirtualVariableStrategy] = {}


def register_strategy(name: str) -> Callable[[Type], Type]:
    """
    Class decorator that registers a strategy under the given variable name.
 
    Usage::
 
        @register_strategy("WIND_SPEED")
        class WindSpeedStrategy:
            def compute(self, ds, path): ...
    """
    def decorator(cls: Type) -> Type:
        _REGISTRY[name.upper()] = cls()
        return cls
    
    return decorator


def get_strategy(name: str) -> VirtualVariableStrategy | None:
    """Return the registered strategy for *name*, or None if it is a raw variable."""
    return _REGISTRY.get(name.upper())