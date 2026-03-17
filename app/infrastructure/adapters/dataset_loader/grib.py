from pathlib import Path
from typing import Final

import xarray as xr

from app.domain.exceptions import DataSourceError
from app.infrastructure.adapters.dataset_loader.base import DatasetLoader

GRID_EXTENSIONS: Final[set[str]] = {".grib", ".grb", ".grib2", ".grb2"}


class GridDatasetLoader(DatasetLoader):
    def _validate(self, path: Path) -> Path:
        self._assert_exists(path)

        if path.suffix.lower() not in GRID_EXTENSIONS:
            raise DataSourceError(f"Not a recognized GRIB file: {path}")

        return path

    def _open(self, path: Path) -> xr.Dataset:
        try:
            return xr.open_dataset(path, engine="cfgrib", decode_timedelta=False)
        except Exception as exc:
            raise DataSourceError(f"Failed to open GRIB file '{path}': {exc}") from exc