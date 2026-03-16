"""
presentation/routers/weather.py

Weather map endpoints.

A single parameterised route replaces the previous duplicated /temperature
and /pressure endpoints.  Adding a new variable requires only a registry
entry in domain/variable_registry.py.
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from app.application.dtos import RenderMapQuery
from app.application.use_cases import RenderWeatherMapUseCase
from app.application.variable_specs.registry import all_variable_names
from app.infrastructure.persistence.database import get_db_session
from app.infrastructure.persistence.repositories.log_repository import SqlAlchemyLogRepository
from app.presentation.schemas import WeatherMapRequest
from sqlalchemy.orm import Session

router = APIRouter(tags=["Weather Maps"])


def _build_use_case(variable: str, request: Request, session: Session) -> RenderWeatherMapUseCase:
    from app.application.use_cases import RenderWeatherMapUseCase
    container = request.app.state.container
    reader = container.get_reader_for_variable(variable)
    log_repo = SqlAlchemyLogRepository(session)
    return RenderWeatherMapUseCase(
        reader=reader,
        renderer=container.renderer,
        log_repo=log_repo,
        cache=container.cache,
        bbox=container.bbox,
    )


@router.get(
    "/weather/{variable}",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}},
        404: {"description": "Variable or timestamp not found"},
        422: {"description": "Invalid query parameters"},
        500: {"description": "Data source error"},
    },
    summary="Render a weather variable map",
    description=(
        "Returns a PNG map for the given variable and timestamp.\n\n"
        f"Available variables: `{'`, `'.join(all_variable_names())}`"
    ),
)
def get_weather_map(
    variable: str,
    request: Request,
    time: str = Query(..., description="ISO 8601 datetime, e.g. 2025-01-29T00:00"),
    session: Session = Depends(get_db_session),
) -> Response:
    validated = WeatherMapRequest(time=time)
    use_case = _build_use_case(variable, request, session)
    png = use_case.execute(RenderMapQuery(variable=variable, time=validated.time))
    return Response(content=png, media_type="image/png")


# ---------------------------------------------------------------------------
# Backward-compatible aliases so existing clients don't break
# ---------------------------------------------------------------------------

@router.get("/temperature", response_class=Response, include_in_schema=False)
def get_temperature(
    request: Request,
    time: str = Query(...),
    session: Session = Depends(get_db_session),
) -> Response:
    validated = WeatherMapRequest(time=time)
    use_case = _build_use_case("temperature", request, session)
    png = use_case.execute(RenderMapQuery(variable="temperature", time=validated.time))
    return Response(content=png, media_type="image/png")


@router.get("/pressure", response_class=Response, include_in_schema=False)
def get_pressure(
    request: Request,
    time: str = Query(...),
    session: Session = Depends(get_db_session),
) -> Response:
    validated = WeatherMapRequest(time=time)
    use_case = _build_use_case("pressure", request, session)
    png = use_case.execute(RenderMapQuery(variable="pressure", time=validated.time))
    return Response(content=png, media_type="image/png")
