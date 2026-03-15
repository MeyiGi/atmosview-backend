from __future__ import annotations
from pathlib import Path
from typing import Protocol

import numpy as np
import xarray as xr

from app.domain.entities import WeatherGrid, WrfMeta
from app.domain.exceptions import VariableNotFoundError
from app.domain.interfaces import WrfDataReader
from app.infrastructure.adapters.dataset_loader import WrfDatasetLoader
from . import coord_extractor, time_parser
from .file_locator import WrfFileLocator

_WRFOUT_PREFIX = "wrfout_d01_"


class VirtualVariableStrategy(Protocol):
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray: ...


class SumFieldsStrategy:
    def __init__(self, *fields: str) -> None:
        self._fields = fields

    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        present = [f for f in self._fields if f in ds]
        if not present:
            raise VariableNotFoundError(
                f"None of {self._fields} found in '{path.name}'. "
                f"Available: {list(ds.data_vars)}"
            )
        arrays = [_read_single(ds, f, path) for f in present]
        return sum(arrays[1:], arrays[0])


class WindSpeedStrategy:
    """sqrt(U10² + V10²)"""
    def __init__(self, u: str, v: str) -> None:
        self._u = u
        self._v = v

    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        u = _read_single(ds, self._u, path)
        v = _read_single(ds, self._v, path)
        return np.sqrt(u ** 2 + v ** 2)


class WindDirectionStrategy:
    """Meteorological wind direction in degrees (0° = from North)"""
    def __init__(self, u: str, v: str) -> None:
        self._u = u
        self._v = v

    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        u = _read_single(ds, self._u, path)
        v = _read_single(ds, self._v, path)
        return (270 - np.degrees(np.arctan2(v, u))) % 360


_VIRTUAL_VARIABLES: dict[str, VirtualVariableStrategy] = {
    "PRECIPITATION":  SumFieldsStrategy("RAINC", "RAINNC"),
    "WIND_SPEED":     WindSpeedStrategy("U10", "V10"),
    "WIND_DIRECTION": WindDirectionStrategy("U10", "V10"),
}


def _read_single(ds: xr.Dataset, variable: str, path: Path) -> np.ndarray:
    if variable not in ds:
        raise VariableNotFoundError(
            f"Variable '{variable}' not found in '{path.name}'. "
            f"Available: {list(ds.data_vars)}"
        )
    values = ds[variable].values
    return values[0] if values.ndim == 3 else values


class WrfReaderAdapter(WrfDataReader):

    def __init__(self, wrf_dir: str) -> None:
        self._locator = WrfFileLocator(wrf_dir)

    def read_variable(self, wrf_variable: str, time: str | None) -> WeatherGrid:
        path = self._locator.resolve(time)
        ds = WrfDatasetLoader(path).get()
        values = self._resolve(ds, wrf_variable, path)
        lats, lons = coord_extractor.extract(ds)
        return WeatherGrid(
            lats=lats, lons=lons, values=values,
            variable=wrf_variable,
            time=time_parser.to_datetime(self._time_token(path)),
        )

    def get_meta(self) -> WrfMeta:
        files = self._locator.list_sorted()
        ds = WrfDatasetLoader(files[-1]).get()
        lats, lons = coord_extractor.extract(ds)
        return WrfMeta(
            bounds=((float(lats.min()), float(lons.min())),
                    (float(lats.max()), float(lons.max()))),
            available_times=[self._time_token(f) for f in files],
        )

    @staticmethod
    def _time_token(path: Path) -> str:
        return path.name.removeprefix(_WRFOUT_PREFIX)

    @staticmethod
    def _resolve(ds: xr.Dataset, variable: str, path: Path) -> np.ndarray:
        strategy = _VIRTUAL_VARIABLES.get(variable.upper())
        if strategy is not None:
            return strategy.compute(ds, path)
        return _read_single(ds, variable, path)