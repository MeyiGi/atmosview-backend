"""
presentation/routers/logs.py

Request log endpoint.
"""

from fastapi import APIRouter, Depends

from app.application.use_cases import GetRequestLogsUseCase
from app.presentation.dependencies import get_logs_use_case
from app.presentation.schemas import RequestLogResponse

router = APIRouter(tags=["Logs"])


@router.get(
    "/logs",
    response_model=list[RequestLogResponse],
    summary="Recent request logs",
    description="Returns the most recent API request logs, ordered newest first.",
)
def get_logs(
    limit: int = 50,
    use_case: GetRequestLogsUseCase = Depends(get_logs_use_case),
) -> list[RequestLogResponse]:
    entries = use_case.execute(limit=limit)
    return [RequestLogResponse(**vars(entry)) for entry in entries]
