"""
infrastructure/persistence/repositories/log_repository.py

SQLAlchemy implementation of the RequestLogRepository port.
All ORM concerns stay in this file.
"""

from sqlalchemy.orm import Session

from app.domain.interfaces import RequestLogRepository
from app.infrastructure.persistence.models.request_log import RequestLogOrm


class SqlAlchemyLogRepository(RequestLogRepository):
    """Persists request logs via SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        endpoint: str,
        requested_time: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        log = RequestLogOrm(
            endpoint=endpoint,
            requested_time=requested_time,
            status=status,
            error_message=error_message,
        )
        self._session.add(log)
        self._session.commit()

    def get_recent(self, limit: int = 100) -> list[dict]:
        rows = (
            self._session.query(RequestLogOrm)
            .order_by(RequestLogOrm.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "endpoint": row.endpoint,
                "requested_time": row.requested_time,
                "status": row.status,
                "error_message": row.error_message,
                "created_at": row.created_at,
            }
            for row in rows
        ]
