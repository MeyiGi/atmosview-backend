import numpy as np
from dataclasses import dataclass
from typing import Callable

ArrayTransform = Callable[[np.ndarray], np.ndarray]
LevelsBuilder = Callable[[np.ndarray], np.ndarray]

def identity(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)

def kelvin_to_celsius(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float) / 273.15

def pascal_to_hpa(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float) / 100.0

def smooth_100(values: np.ndarray) -> np.ndarray:
    vmin = float(np.nanmin(values))
    vmax = float(np.nanmax(values))
    if np.isclose(vmin, vmax):
        vmax = vmin + 1.0
    return np.linspace(vmin, vmax, 100)

@dataclass
class ScalarRenderSpec:
    title: str
    unit_label: str
    cmap: str
    transform: ArrayTransform = identity
    levels_builder: LevelsBuilder = smooth_100
    extend: str = "neither"