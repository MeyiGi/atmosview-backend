from pathlib import Path

import xarray as xr

from app.domain.exceptions import DataSourceError
from app.infrastructure.adapters.dataset_loader.base import DatasetLoader


class WrfDatasetLoader(DatasetLoader):
    def _validate(self, path: Path) -> Path:
        self._assert_exists(path)
        return path

    def _open(self, path: Path) -> xr.Dataset:
        try:
            return xr.open_dataset(path)
        except Exception as exc:
            raise DataSourceError(f"Cannot open WRF file '{path}': {exc}") from exc