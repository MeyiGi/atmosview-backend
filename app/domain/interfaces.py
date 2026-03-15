"""
domain/interfaces.py

Abstract ports that define what the application layer needs from the
outside world.  Infrastructure adapters implement these; use cases depend
only on these abstractions — never on concrete implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities import BoundingBox, WeatherGrid, WrfMeta
from .entities import VariableSpec


# ---------------------------------------------------------------------------
# Weather data reading port
# ---------------------------------------------------------------------------


class WeatherDataReader(ABC):
    """
    Port for reading gridded weather data from any source (GRIB, WRF, NetCDF…).
    A concrete adapter wraps a specific file format or API behind this contract.
    """

    @abstractmethod
    def read(self, variable: str, time: datetime, bbox: BoundingBox) -> WeatherGrid:
        """
        Load data for *variable* at *time* clipped to *bbox*.

        Raises:
            DataSourceError:    if the underlying source cannot be opened.
            TimeNotFoundError:  if *time* is not in the dataset.
            VariableNotFoundError: if *variable* is not available.
        """

    @abstractmethod
    def available_times(self) -> list[datetime]:
        """Return all timestamps present in the source."""


# ---------------------------------------------------------------------------
# Rendering port
# ---------------------------------------------------------------------------


# class WeatherRenderer(ABC):
#     """Port for turning a WeatherGrid into a visual representation."""

#     @abstractmethod
#     def render_png(self, grid: WeatherGrid) -> bytes:
#         """Return PNG-encoded bytes for the given grid."""


# ---------------------------------------------------------------------------
# WRF-specific reader port
# ---------------------------------------------------------------------------


class WrfDataReader(ABC):
    """
    Port for reading WRF model output.  Separated from the generic reader
    because WRF files have a different selection model (filename encodes time).
    """

    @abstractmethod
    def read_variable(self, wrf_variable: str, time: str | None) -> WeatherGrid:
        """
        Read a WRF variable from the output file matching *time*
        (or the latest file when *time* is None).

        Raises:
            DataSourceError:        if no wrfout files are found or the file
                                    cannot be opened.
            VariableNotFoundError:  if *wrf_variable* is absent.
        """

    @abstractmethod
    def get_meta(self) -> WrfMeta:
        """Return metadata for the current WRF domain."""


# ---------------------------------------------------------------------------
# Logging port
# ---------------------------------------------------------------------------


class RequestLogRepository(ABC):
    """Port for persisting request audit logs."""

    @abstractmethod
    def save(
        self,
        endpoint: str,
        requested_time: str,
        status: str,
        error_message: str | None = None,
    ) -> None: ...

    @abstractmethod
    def get_recent(self, limit: int) -> list[dict]: ...


# ---------------------------------------------------------------------------
# Cache port
# ---------------------------------------------------------------------------


class DataCache(ABC):
    """
    Port for an in-process key/value cache.
    Keeps the application layer independent of the caching mechanism
    (dict, LRU, Redis, …).
    """

    @abstractmethod
    def get(self, key: str) -> object | None: ...

    @abstractmethod
    def set(self, key: str, value: object) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...


# ---------------------------------------------------------------------------
# Render wind in
# ---------------------------------------------------------------------------

class WeatherRenderer(ABC):

    @abstractmethod
    def render_png(self, grid: WeatherGrid) -> bytes: ...

    @abstractmethod
    def render_wind_png(self, u_grid: WeatherGrid, v_grid: WeatherGrid) -> bytes:
        """Render wind speed + direction arrows from U and V component grids."""