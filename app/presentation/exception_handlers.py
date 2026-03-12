"""
presentation/exception_handlers.py

Maps domain exceptions to HTTP responses.
This is the only place that knows about both FastAPI and domain exceptions.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    DataSourceError,
    TimeNotFoundError,
    VariableNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(VariableNotFoundError)
    async def variable_not_found(request: Request, exc: VariableNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TimeNotFoundError)
    async def time_not_found(request: Request, exc: TimeNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DataSourceError)
    async def data_source_error(request: Request, exc: DataSourceError):
        return JSONResponse(status_code=500, content={"detail": str(exc)})
