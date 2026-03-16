"""
presentation/dependencies.py

FastAPI dependency providers.

Each function retrieves the relevant singleton from app.state.container
and constructs the per-request objects that need a DB session.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.application.use_cases import (
    GetRequestLogsUseCase,
    GetWrfMetaUseCase,
    RenderWrfMapUseCase,
)
from app.application.use_cases import RenderWrfWindUseCase

from app.infrastructure.container import Container
from app.infrastructure.persistence.database import get_db_session
from app.infrastructure.persistence.repositories.log_repository import SqlAlchemyLogRepository



def get_container(request: Request) -> Container:
    return request.app.state.container


def get_log_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyLogRepository:
    return SqlAlchemyLogRepository(session)


def render_wrf_map_use_case(
    container: Container = Depends(get_container),
    log_repo: SqlAlchemyLogRepository = Depends(get_log_repo),
) -> RenderWrfMapUseCase:
    return RenderWrfMapUseCase(
        wrf_reader=container.wrf_reader,
        renderer=container.renderer,
        log_repo=log_repo,
    )


def get_wrf_meta_use_case(
    container: Container = Depends(get_container),
) -> GetWrfMetaUseCase:
    return GetWrfMetaUseCase(wrf_reader=container.wrf_reader)


def get_logs_use_case(
    log_repo: SqlAlchemyLogRepository = Depends(get_log_repo),
) -> GetRequestLogsUseCase:
    return GetRequestLogsUseCase(log_repo=log_repo)


def render_wrf_wind_use_case(
    container: Container = Depends(get_container),
    log_repo: SqlAlchemyLogRepository = Depends(get_log_repo),
) -> RenderWrfWindUseCase:
    return RenderWrfWindUseCase(
        wrf_reader=container.wrf_reader,
        renderer=container.renderer,
        log_repo=log_repo,
    )