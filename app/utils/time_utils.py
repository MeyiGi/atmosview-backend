"""
time_utils.py

Just some helpers for dealing with datetime strings and conversions.
I kept running into the same parsing logic in multiple places so I pulled it out here.
"""

from datetime import datetime


def parse_iso_datetime(time_str: str) -> datetime | None:
    """
    Try to parse a datetime string in ISO 8601 format.
    Returns None if it fails instead of blowing up — let the caller decide what to do.

    Examples:
        "2025-01-29T00:00"     -> works
        "2025-01-29 00:00:00"  -> works
        "not-a-date"           -> returns None
    """
    if not time_str or not isinstance(time_str, str):
        return None

    cleaned = time_str.strip()

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None