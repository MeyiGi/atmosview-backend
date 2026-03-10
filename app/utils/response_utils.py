"""
response_utils.py

Helpers for building consistent API responses and error messages.
Mostly so I don't have to remember the exact HTTPException syntax every time.
"""

from fastapi import HTTPException


def raise_not_found(detail: str) -> None:
    """Shortcut for 404. Just saves a little boilerplate."""
    raise HTTPException(status_code=404, detail=detail)


def raise_bad_request(detail: str) -> None:
    """Shortcut for 400."""
    raise HTTPException(status_code=400, detail=detail)


def raise_server_error(detail: str) -> None:
    """Shortcut for 500 — something blew up on our end."""
    raise HTTPException(status_code=500, detail=detail)


def raise_unprocessable(field: str, value: str, hint: str = "") -> None:
    """
    422 for bad input values. Includes field name so the caller knows what went wrong.

    Example:
        raise_unprocessable("time", "not-a-date", "Expected ISO 8601 format")
    """
    msg = f"Invalid value for '{field}': '{value}'."
    if hint:
        msg += f" {hint}"
    raise HTTPException(status_code=422, detail=msg)