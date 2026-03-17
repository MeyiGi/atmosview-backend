"""
application/dtos.py

Data Transfer Objects that cross the boundary between use cases and
the presentation layer.  Pure dataclasses — no framework, no ORM.
"""

from dataclasses import dataclass
from datetime import datetime

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
