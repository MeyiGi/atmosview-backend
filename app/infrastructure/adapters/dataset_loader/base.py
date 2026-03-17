from abc import ABC, abstractmethod
from pathlib import Path

import xarray as xr

from app.domain.exceptions import DataSourceError


class DatasetLoader(ABC):
    def __init__(self, path: Path) -> None:
        self._path = self._validate(path)

    def get(self) -> xr.Dataset:
        return self._open(self._path)

    @abstractmethod
    def _validate(self, path: Path) -> Path:
        ...

    @abstractmethod
    def _open(self, path: Path) -> xr.Dataset:
        ...

    @staticmethod
    def _assert_exists(path: Path) -> None:
        if not path.exists():
            raise DataSourceError(f"File not found: {path}")