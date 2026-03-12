import glob
import os
from datetime import datetime

import numpy as np
import xarray as xr

from app.domain.entities import WeatherGrid, WrfMeta
from app.domain.exceptions import DataSourceError, VariableNotFoundError
from app.domain.interfaces import WrfDataReader

_WRFOUT_GLOB = "wrfout_d01_*"


class WrfReaderAdapter(WrfDataReader):
    def __init__(self, wrf_dir: str) -> None:
        self._wrf_dir = wrf_dir

    def read_variable(self, wrf_variable: str, time: str | None) -> WeatherGrid:
        path = self._resolve_path(time)
        ds = self._open(path)

        if wrf_variable not in ds:
            raise VariableNotFoundError(
                f"Variable '{wrf_variable}' not found in '{os.path.basename(path)}'. "
                f"Available: {list(ds.data_vars)}"
            )

        raw = ds[wrf_variable].values
        data_2d = raw[0] if raw.ndim == 3 else raw

        lats, lons = self._extract_coords(ds)
        timestamp_str = os.path.basename(path).replace("wrfout_d01_", "")

        return WeatherGrid(
            lats=lats,
            lons=lons,
            values=data_2d,
            variable=wrf_variable,
            time=self._parse_wrf_time(timestamp_str),
        )

    def get_meta(self) -> WrfMeta:
        files = self._list_files()
        latest = files[-1]
        ds = self._open(latest)

        lats, lons = self._extract_coords(ds)
        south, north = float(lats.min()), float(lats.max())
        west, east = float(lons.min()), float(lons.max())

        times = [os.path.basename(f).replace("wrfout_d01_", "") for f in files]
        return WrfMeta(
            bounds=((south, west), (north, east)),
            available_times=times,
        )

    def _list_files(self) -> list[str]:
        files = sorted(glob.glob(os.path.join(self._wrf_dir, _WRFOUT_GLOB)))
        if not files:
            raise DataSourceError(f"No wrfout files found in '{self._wrf_dir}'")
        return files

    def _resolve_path(self, time: str | None) -> str:
        if time is None:
            return self._list_files()[-1]

        normalized_time = self._normalize_time_for_filename(time)
        path = os.path.join(self._wrf_dir, f"wrfout_d01_{normalized_time}")

        if not os.path.exists(path):
            raise DataSourceError(f"WRF output file not found: '{path}'")
        return path

    @staticmethod
    def _normalize_time_for_filename(time_str: str) -> str:
        for fmt in (
            "%Y-%m-%d_%H%M%S",
            "%Y-%m-%d_%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.strftime("%Y-%m-%d_%H%M%S")
            except ValueError:
                continue

        raise DataSourceError(
            f"Invalid WRF time format: '{time_str}'. "
            "Expected formats: YYYY-MM-DD_HHMMSS, YYYY-MM-DD_HH:MM:SS, or YYYY-MM-DDTHH:MM:SS"
        )

    @staticmethod
    def _open(path: str) -> xr.Dataset:
        try:
            return xr.open_dataset(path)
        except Exception as exc:
            raise DataSourceError(f"Cannot open WRF file '{path}': {exc}") from exc

    @staticmethod
    def _extract_coords(ds: xr.Dataset) -> tuple[np.ndarray, np.ndarray]:
        if "XLAT" not in ds or "XLONG" not in ds:
            raise DataSourceError("XLAT/XLONG coordinates not found in wrfout file.")
        lats = ds["XLAT"].values
        lons = ds["XLONG"].values
        if lats.ndim == 3:
            lats = lats[0]
        if lons.ndim == 3:
            lons = lons[0]
        return lats, lons

    @staticmethod
    def _parse_wrf_time(time_str: str):
        from datetime import datetime

        for fmt in (
            "%Y-%m-%d_%H%M%S",
            "%Y-%m-%d_%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        return datetime(1900, 1, 1)