"""
domain/exceptions.py

Pure domain exceptions — no framework imports, no infrastructure concerns.
These travel upward through the application layer and get mapped to HTTP
errors at the presentation boundary.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class DataSourceError(DomainError):
    """Raised when a weather data source cannot be opened or parsed."""


class TimeNotFoundError(DomainError):
    """Raised when the requested timestamp is not available in the dataset."""


class VariableNotFoundError(DomainError):
    """Raised when the requested variable does not exist in the dataset."""
