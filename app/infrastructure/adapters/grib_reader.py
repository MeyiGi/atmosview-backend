"""
infrastructure/adapters/grib_reader.py

Adapter that implements WeatherDataReader using xarray + cfgrib.

Design notes:
  * The xr.Dataset is opened once per GribReaderAdapter instance and then
    cached on self._ds.  Because adapters are created as application-lifetime
    singletons (via the DI container), this gives true cross-request caching.
  * The adapter is intentionally thin — it only translates between the
    infrastructure concern (xarray / GRIB) and the domain contract
    (WeatherGrid, domain exceptions).
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr

from app.domain.entities import BoundingBox, WeatherGrid
from app.domain.exceptions import DataSourceError, TimeNotFoundError
from app.domain.interfaces import WeatherDataReader

_TIME_COORD_CANDIDATES = ("time", "valid_time")


class GribReaderAdapter(WeatherDataReader):
    """Reads a single GRIB file and exposes it via the WeatherDataReader port."""

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise DataSourceError(f"GRIB file not found: {path}")
        if path.suffix.lower() not in {".grib", ".grb", ".grib2", ".grb2"}:
            raise DataSourceError(f"Not a recognised GRIB extension: {path}")
        self._path = path
        self._ds: xr.Dataset | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def read(self, variable: str, time: datetime, bbox: BoundingBox) -> WeatherGrid:
        ds = self._get_dataset()
        da = self._get_data_array(ds)
        da = self._select_time(da, time)
        da = self._clip_bbox(da, bbox)

        return WeatherGrid(
            lats=da.latitude.values,
            lons=da.longitude.values,
            values=da.values,
            variable=variable,
            time=time,
        )

    def available_times(self) -> list[datetime]:
        ds = self._get_dataset()
        for key in _TIME_COORD_CANDIDATES:
            if key in ds.coords:
                raw = np.ravel(ds.coords[key].values).astype("datetime64[ms]")
                return [v.astype(datetime) for v in raw]
        return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_dataset(self) -> xr.Dataset:
        if self._ds is None:
            try:
                self._ds = xr.open_dataset(
                    self._path, engine="cfgrib", decode_timedelta=False
                )
            except Exception as exc:
                raise DataSourceError(
                    f"Failed to open GRIB file '{self._path}': {exc}"
                ) from exc
        return self._ds

    @staticmethod
    def _get_data_array(ds: xr.Dataset) -> xr.DataArray:
        if not ds.data_vars:
            raise DataSourceError("No data variables found in dataset.")
        return ds[next(iter(ds.data_vars))]

    @staticmethod
    def _select_time(da: xr.DataArray, t: datetime) -> xr.DataArray:
        key = next(
            (k for k in _TIME_COORD_CANDIDATES if k in da.coords and k in da.dims),
            None,
        )
        if key is None:
            return da

        t64 = np.datetime64(t.replace(tzinfo=None), "ns")
        try:
            return da.sel({key: t64}, method="nearest")
        except KeyError:
            available = [
                v.astype("datetime64[ms]").astype(datetime)
                for v in np.ravel(da.coords[key].values)
            ]
            raise TimeNotFoundError(
                f"Requested time {t.isoformat()} not found in dataset. "
                f"Available times: {[x.isoformat() for x in available]}"
            )

    @staticmethod
    def _clip_bbox(da: xr.DataArray, bbox: BoundingBox) -> xr.DataArray:
        lat = da.latitude
        lon = da.longitude

        lat_slice = (
            slice(bbox.lat_min, bbox.lat_max)
            if lat[0] < lat[-1]
            else slice(bbox.lat_max, bbox.lat_min)
        )
        lon_slice = (
            slice(bbox.lon_min, bbox.lon_max)
            if lon[0] < lon[-1]
            else slice(bbox.lon_max, bbox.lon_min)
        )
        return da.sel(latitude=lat_slice, longitude=lon_slice)
