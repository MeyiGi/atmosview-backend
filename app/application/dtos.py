"""
application/dtos.py

Data Transfer Objects that cross the boundary between use cases and
the presentation layer.  Pure dataclasses — no framework, no ORM.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class RenderWindQuery:
    """Input for the combined wind map use case."""
    time: str | None

@dataclass(frozen=True)
class RenderMapQuery:
    """Input for the 'render weather map' use case."""

    variable: str
    time: datetime


@dataclass(frozen=True)
class WrfRenderQuery:
    metric: str
    wrf_variable: str
    time: str | None


@dataclass(frozen=True)
class RequestLogEntry:
    """Read model returned by the logs use case."""

    id: int
    endpoint: str
    requested_time: str
    status: str
    error_message: str | None
    created_at: datetime

@dataclass(frozen=True)
class GridDataResult:
    """
    Grid data for client-side rendering.
    Replaces the PNG byte payload — the frontend draws the colours.

    lats:   1-D list of latitude values (south→north), length M
    lons:   1-D list of longitude values (west→east), length N
    values: 2-D list, shape [M][N], matching lats × lons order.
            None entries represent missing/masked cells.
    """
    variable:  str
    unit:      str
    time:      str                        # ISO-8601 string
    lat_min:   float
    lat_max:   float
    lon_min:   float
    lon_max:   float
    lats:      List[float]
    lons:      List[float]
    values:    List[List[float | None]]   # [lat_idx][lon_idx]