# ── Add this router in  app/presentation/routers/weather_grid.py ────────────
# Then register it in app/main.py:  app.include_router(weather_grid.router)

"""
presentation/routers/weather_grid.py

Grid-data endpoint — returns raw float arrays for client-side rendering.
Mirrors /weather/{variable} but returns JSON instead of PNG.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.dtos import GridDataResult
from app.application.use_cases_grid import GetWeatherGridUseCase
from app.application.variable_specs.registry import all_variable_names
from app.infrastructure.persistence.database import get_db_session
from app.presentation.schemas import WeatherMapRequest

router = APIRouter(tags=["Weather Grid"])

# Reuse the same unit labels defined per-variable in the variable specs.
# The use case will pull the unit from VariableSpec.unit_label.
_UNITS: dict[str, str] = {
    "temperature":    "°C",
    "pressure":       "hPa",
    "precipitation":  "mm",
    "wind_speed":     "m/s",
    "wind_direction": "°",
    "humidity":       "kg/kg",
}


def _build_grid_use_case(
    variable: str, request: Request, session: Session
) -> GetWeatherGridUseCase:
    container = request.app.state.container
    reader    = container.get_reader_for_variable(variable)
    return GetWeatherGridUseCase(
        reader=reader,
        bbox=container.bbox,
        cache=container.cache,
        unit=_UNITS.get(variable, ""),
    )


@router.get(
    "/weather/{variable}/grid",
    summary="Raw grid data for client-side rendering",
    description=(
        "Returns the float value grid (lats × lons × values) for a weather "
        "variable. The frontend uses this to render a colour field directly "
        "on a canvas element — no server-side matplotlib involved.\n\n"
        f"Available variables: `{'`, `'.join(all_variable_names())}`"
    ),
    responses={
        200: {
            "content": {"application/json": {}},
            "description": "Grid data with lats[], lons[], values[][] arrays",
        },
        404: {"description": "Variable or timestamp not found"},
        422: {"description": "Invalid query parameters"},
    },
)
def get_weather_grid(
    variable: str,
    request:  Request,
    time:     str = Query(..., description="ISO 8601 datetime, e.g. 2025-01-29T00:00"),
    session:  Session = Depends(get_db_session),
) -> JSONResponse:
    validated   = WeatherMapRequest(time=time)
    use_case    = _build_grid_use_case(variable, request, session)
    result: GridDataResult = use_case.execute(variable, validated.time)

    return JSONResponse(content={
        "variable":  result.variable,
        "unit":      result.unit,
        "time":      result.time,
        "lat_min":   result.lat_min,
        "lat_max":   result.lat_max,
        "lon_min":   result.lon_min,
        "lon_max":   result.lon_max,
        "lats":      result.lats,
        "lons":      result.lons,
        "values":    result.values,
    })
