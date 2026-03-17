from datetime import datetime
from pathlib import Path

import xarray as xr
from app.domain.exceptions import DataSourceError
from app.domain.interfaces import WeatherDataReader

from app.domain.entities import BoundingBox, WeatherGrid
from app.infrastructure.adapters.dataset_loader.base import DatasetLoader
from app.infrastructure.adapters.dataset_loader.grib import GridDatasetLoader

from . import bbox_clipper, time_selector


class GribReaderAdapter(WeatherDataReader):
    def __init__(self, path: Path) -> None:
        self._loader: DatasetLoader = GridDatasetLoader(path)

    def read(self, variable: str, time: datetime, bbox: BoundingBox) -> WeatherGrid:
        da = _first_variable(self._loader.get())
        da = time_selector.select(da, time)
        da = bbox_clipper.clip(da, bbox)
        return WeatherGrid(
            lats=da.latitude.values,
            lons=da.longitude.values,
            values=da.values,
            variable=variable,
            time=time,
        )
    
    def available_times(self) -> list[datetime]:
        return time_selector.available(self._loader.get())
    
def _first_variable(ds: xr.Dataset) -> xr.DataArray:
    """
    Return the first data variable in the dataset.
 
    GRIB files typically contain a single variable per file (e.g. temperature,
    wind speed). We don't require the caller to know its internal name.
    """
    if not ds.data_vars:
        raise DataSourceError("No data variables found in GRID dataset.")
    
    return ds[next(iter(ds.data_vars))]