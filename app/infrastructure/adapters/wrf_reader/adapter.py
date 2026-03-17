from pathlib import Path
 
import numpy as np
import xarray as xr
 
from app.domain.entities import WeatherGrid, WrfMeta
from app.domain.interfaces import WrfDataReader

from app.infrastructure.adapters.dataset_loader.base import DatasetLoader
from app.infrastructure.adapters.dataset_loader.wrf import WrfDatasetLoader
from . import coord_extractor, time_parser
from .file_locator import WrfFileLocator
from .helpers import read_single
from .registry import get_strategy
 

_WRFOUT_PREFIX = "wrfout_d01_"

class WrfReaderAdapter(WrfDataReader):

    def __init__(self, wrf_dir: str) -> None:
        self._locator = WrfFileLocator(wrf_dir)

    def read_variable(self, wrf_variable: str, time: str | None) -> WeatherGrid:
        path = self._locator.resolve(time)
        ds = WrfDatasetLoader(path).get()
        values = self._read_values(ds, wrf_variable, path)
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
    def _read_values(ds: xr.Dataset, variable: str, path: Path) -> np.ndarray:
        strategy = get_strategy(variable)
        if strategy is not None:
            return strategy.compute(ds, path)
        return read_single(ds, variable, path)