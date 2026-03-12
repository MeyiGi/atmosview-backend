"""
presentation/schemas.py

Pydantic models for request validation and response serialisation.
These exist only at the presentation boundary — they never enter the
application or domain layers.
"""

from datetime import datetime

from pydantic import BaseModel, field_validator


class WeatherMapRequest(BaseModel):
    """Query parameters for weather map endpoints."""

    time: datetime

    @field_validator("time", mode="before")
    @classmethod
    def parse_iso_time(cls, v: str | datetime) -> datetime:
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v).strip())
        except ValueError:
            raise ValueError(
                f"Invalid time format: '{v}'. "
                "Expected ISO 8601, e.g. '2025-01-29T00:00'."
            )


class RequestLogResponse(BaseModel):
    id: int
    endpoint: str
    requested_time: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
