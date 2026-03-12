"""
infrastructure/persistence/models/request_log.py

SQLAlchemy ORM model.  Only the infrastructure layer knows this exists.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RequestLogOrm(Base):
    """Persists every API request for usage tracking and debugging."""

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, nullable=False)
    requested_time = Column(String, nullable=False)   # kept as String for flexibility
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
