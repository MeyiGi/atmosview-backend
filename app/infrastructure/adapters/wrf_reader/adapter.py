"""
WrfReaderAdapter — implements WrfDataReader for WRF output files.

The virtual variable "PRECIPITATION" is resolved here as RAINC + RAINNC.
Domain and application layers stay free of WRF-specific field names.
"""

import os
from pathlib import Path

import numpy as np
import xarray as xr

from app.domain.entities import WeatherGrid, WrfMeta
from app.domain.exceptions import VariableNotFoundError
from app.domain.interfaces import WrfDataReader
from app.infrastructure.adapters.dataset_loader import WrfDatasetLoader
from . import coord_extractor, time_parser
from .file_locator import WrfFileLocator

_WRFOUT_PREFIX = "wrfout_d01_"

# Virtual variables: logical name → WRF fields to sum
_VIRTUAL_VARIABLES: dict[str, tuple[str, ...]] = {
    "PRECIPITATION": ("RAINC", "RAINNC"),
}


class WrfReaderAdapter(WrfDataReader):

    def __init__(self, wrf_dir: str) -> None:
        self._locator = WrfFileLocator(wrf_dir)

    def read_variable(self, wrf_variable: str, time: str | None) -> WeatherGrid:
        path = self._locator.resolve(time)
        ds = self._load(path)
        values = self._extract_values(ds, wrf_variable, path)
        lats, lons = coord_extractor.extract(ds)
        return WeatherGrid(
            lats=lats,
            lons=lons,
            values=values,
            variable=wrf_variable,
            time=time_parser.to_datetime(self._time_token(path)),
        )

    def get_meta(self) -> WrfMeta:
        files = self._locator.list_sorted()
        lats, lons = coord_extractor.extract(self._load(files[-1]))
        return WrfMeta(
            bounds=(
                (float(lats.min()), float(lons.min())),
                (float(lats.max()), float(lons.max())),
            ),
            available_times=[self._time_token(f) for f in files],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load(path: Path) -> xr.Dataset:
        return WrfDatasetLoader(path).get()

    @staticmethod
    def _time_token(path: Path) -> str:
        return path.name.removeprefix(_WRFOUT_PREFIX)

    @classmethod
    def _extract_values(cls, ds: xr.Dataset, variable: str, path: Path) -> np.ndarray:
        components = _VIRTUAL_VARIABLES.get(variable.upper())
        if components is not None:
            return cls._sum_components(ds, components, path)
        return cls._read_single(ds, variable, path)

    @staticmethod
    def _read_single(ds: xr.Dataset, variable: str, path: Path) -> np.ndarray:
        if variable not in ds:
            raise VariableNotFoundError(
                f"Variable '{variable}' not found in '{path.name}'. "
                f"Available: {list(ds.data_vars)}"
            )
        values = ds[variable].values
        return values[0] if values.ndim == 3 else values

    @classmethod
    def _sum_components(
        cls, ds: xr.Dataset, components: tuple[str, ...], path: Path
    ) -> np.ndarray:
        present = [c for c in components if c in ds]
        if not present:
            raise VariableNotFoundError(
                f"None of {components} found in '{path.name}'. "
                f"Available: {list(ds.data_vars)}"
            )
        arrays = [cls._read_single(ds, c, path) for c in present]
        return sum(arrays[1:], arrays[0])  # type: ignore[return-value]