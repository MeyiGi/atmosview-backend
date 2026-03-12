"""
domain/entities.py

Lightweight value objects that carry meaning across layer boundaries.
These are plain dataclasses — no ORM, no Pydantic, no framework.
"""

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    """Geographic region defined by lat/lon boundaries."""

    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


@dataclass(frozen=True)
class WeatherGrid:
    """
    Raw spatial weather data for a single variable at a single timestamp.
    Immutable so it can be safely passed between layers and cached.
    """

    lats: np.ndarray
    lons: np.ndarray
    values: np.ndarray
    variable: str
    time: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WeatherGrid):
            return False
        return (
            self.variable == other.variable
            and self.time == other.time
            and np.array_equal(self.lats, other.lats)
            and np.array_equal(self.lons, other.lons)
            and np.array_equal(self.values, other.values)
        )

    def __hash__(self) -> int:  # type: ignore[override]
        return hash((self.variable, self.time))


@dataclass(frozen=True)
class VariableSpec:
    """
    Describes how a named weather variable should be read and rendered.
    Used by the variable registry to drive generic endpoint handling.
    """

    name: str | None = None
    colormap: str | None = None
    unit_label: str | None = None


@dataclass(frozen=True)
class WrfMeta:
    """Domain representation of WRF domain metadata."""

    bounds: tuple[tuple[float, float], tuple[float, float]]  # [[S,W],[N,E]]
    available_times: list[str]
