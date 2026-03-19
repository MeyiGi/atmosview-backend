# ── Paste this file as  app/application/use_cases_grid.py ───────────────────
# (a separate file keeps grid logic clean; import the classes in main.py / routers)

"""
application/use_cases_grid.py

Two use cases that return raw WeatherGrid data as GridDataResult DTOs
instead of rendered PNG bytes.  The frontend owns all colour mapping.

Both use cases follow the same pattern:
    read grid  →  convert numpy arrays to Python lists  →  return DTO
No renderer, no matplotlib, no bytes.
"""

import logging
from datetime import datetime
from typing import List, Optional

import numpy as np

from app.application.dtos import GridDataResult
from app.application.variable_specs.registry import get_variable_spec
from app.domain.entities import BoundingBox
from app.domain.interfaces import DataCache, WeatherDataReader, WrfDataReader

logger = logging.getLogger(__name__)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _to_float_list(arr: np.ndarray) -> List[float]:
    """Convert a 1-D numpy array to a plain Python float list."""
    return [float(v) for v in arr]


def _convert_units(variable: str, arr: np.ndarray) -> np.ndarray:
    """
    Convert raw GRIB units to the display units expected by the frontend.
      temperature : K  → °C   (subtract 273.15)
      pressure    : Pa → hPa  (divide by 100)
    """
    if variable == "temperature":
        # GRIB files store temperature in Kelvin; frontend expects Celsius
        return arr - 273.15
    if variable == "pressure":
        # GRIB files store pressure in Pascals; frontend expects hPa
        return arr / 100.0
    return arr


def _to_2d_list(arr: np.ndarray) -> List[List[Optional[float]]]:
    """
    Convert a 2-D numpy array (or masked array) to a nested Python list.
    NaN / masked cells become None so JSON serialisation is clean.
    """
    if isinstance(arr, np.ma.MaskedArray):
        arr = arr.filled(np.nan)

    result: List[List[Optional[float]]] = []
    for row in arr:
        result.append([
            None if np.isnan(v) else round(float(v), 6)
            for v in row
        ])
    return result


def _cache_key(prefix: str, variable: str, time_str: str) -> str:
    return f"grid:{prefix}:{variable}:{time_str}"


# ─── GFS / GRIB grid use case ────────────────────────────────────────────────

class GetWeatherGridUseCase:
    """
    Returns the full WeatherGrid for a named GFS variable as a GridDataResult.

    The result is cached in-memory (same cache as the PNG renderer).
    Cache keys are prefixed with 'grid:' to avoid collisions.
    """

    def __init__(
        self,
        reader: WeatherDataReader,
        bbox: BoundingBox,
        cache: DataCache,
        unit: str,
    ) -> None:
        self._reader = reader
        self._bbox   = bbox
        self._cache  = cache
        self._unit   = unit

    def execute(self, variable: str, time: datetime) -> GridDataResult:
        time_str  = time.isoformat()
        cache_key = _cache_key("gfs", variable, time_str)

        cached = self._cache.get(cache_key)
        if isinstance(cached, GridDataResult):
            return cached

        spec = get_variable_spec(variable)
        grid = self._reader.read(spec.name, time, self._bbox)

        # Convert raw GRIB units (K, Pa) to display units (°C, hPa)
        converted_values = _convert_units(variable, grid.values)

        result = GridDataResult(
            variable=variable,
            unit=self._unit or (spec.unit_label or ""),
            time=time_str,
            lat_min=float(grid.lats.min()),
            lat_max=float(grid.lats.max()),
            lon_min=float(grid.lons.min()),
            lon_max=float(grid.lons.max()),
            lats=_to_float_list(
                grid.lats[:, 0] if grid.lats.ndim == 2 else grid.lats
            ),
            lons=_to_float_list(
                grid.lons[0, :] if grid.lons.ndim == 2 else grid.lons
            ),
            values=_to_2d_list(grid.values),
        )

        self._cache.set(cache_key, result)
        return result


# ─── WRF grid use case ───────────────────────────────────────────────────────

class GetWrfGridUseCase:
    """
    Returns WRF model output for a variable as a GridDataResult.
    """

    # Map WRF metric names → WRF variable names (mirrors the router)
    _METRIC_TO_WRF: dict[str, str] = {
        "temperature":   "T2",
        "pressure":      "PSFC",
        "precipitation": "PRECIPITATION",
        "humidity":      "HUMIDITY",
    }

    # Units for each WRF metric
    _UNITS: dict[str, str] = {
        "temperature":   "°C",
        "pressure":      "hPa",
        "precipitation": "mm",
        "wind_speed":    "m/s",
        "humidity":      "kg/kg",
        "wind":          "m/s",
    }

    def __init__(self, wrf_reader: WrfDataReader) -> None:
        self._wrf_reader = wrf_reader

    def execute(self, metric: str, time: Optional[str]) -> GridDataResult:
        wrf_variable = self._METRIC_TO_WRF.get(metric, metric.upper())
        grid = self._wrf_reader.read_variable(wrf_variable, time)

        return GridDataResult(
            variable=metric,
            unit=self._UNITS.get(metric, ""),
            time=time or "latest",
            lat_min=float(grid.lats.min()),
            lat_max=float(grid.lats.max()),
            lon_min=float(grid.lons.min()),
            lon_max=float(grid.lons.max()),
            lats=_to_float_list(
                grid.lats[:, 0] if grid.lats.ndim == 2 else grid.lats
            ),
            lons=_to_float_list(
                grid.lons[0, :] if grid.lons.ndim == 2 else grid.lons
            ),
            values=_to_2d_list(grid.values),
        )
