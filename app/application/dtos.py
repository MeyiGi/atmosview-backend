"""
application/dtos.py

Data Transfer Objects that cross the boundary between use cases and
the presentation layer.  Pure dataclasses — no framework, no ORM.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RenderMapQuery:
    """Input for the 'render weather map' use case."""

    variable: str
    time: datetime


@dataclass(frozen=True)
class WrfRenderQuery:
    """Input for the 'render WRF map' use case."""

    wrf_variable: str   # raw WRF field name, e.g. "T2", "PSFC"
    display_name: str   # human-readable name shown in the plot title
    unit_label: str     # colour-bar label
    time: str | None    # WRF filename timestamp or None → latest


@dataclass(frozen=True)
class RequestLogEntry:
    """Read model returned by the logs use case."""

    id: int
    endpoint: str
    requested_time: str
    status: str
    error_message: str | None
    created_at: datetime
