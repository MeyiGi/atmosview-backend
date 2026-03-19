# ── Add this router as  app/presentation/routers/wrf_grid.py ────────────────
# Register in app/main.py:  app.include_router(wrf_grid.router)

"""
presentation/routers/wrf_grid.py

WRF grid-data endpoints — raw float arrays for client-side canvas rendering.
One route per metric, delegating to GetWrfGridUseCase.
"""

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.dtos import GridDataResult
from app.application.use_cases_grid import GetWrfGridUseCase

router = APIRouter(prefix="/wrf", tags=["WRF Grid"])

_TIME_DESC = (
    "WRF filename timestamp, e.g. 2026-03-12_120000. "
    "Omit for the latest available file."
)


def _use_case(request: Request) -> GetWrfGridUseCase:
    return GetWrfGridUseCase(wrf_reader=request.app.state.container.wrf_reader)


def _resp(result: GridDataResult) -> JSONResponse:
    return JSONResponse(content={
        "variable": result.variable, "unit":    result.unit,
        "time":     result.time,     "lat_min": result.lat_min,
        "lat_max":  result.lat_max,  "lon_min": result.lon_min,
        "lon_max":  result.lon_max,  "lats":    result.lats,
        "lons":     result.lons,     "values":  result.values,
    })


@router.get("/temperature/grid", summary="WRF temperature grid data")
def wrf_temperature_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    return _resp(_use_case(request).execute("temperature", time))


@router.get("/pressure/grid", summary="WRF pressure grid data")
def wrf_pressure_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    return _resp(_use_case(request).execute("pressure", time))


@router.get("/precipitation/grid", summary="WRF precipitation grid data")
def wrf_precipitation_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    return _resp(_use_case(request).execute("precipitation", time))


@router.get("/humidity/grid", summary="WRF humidity grid data")
def wrf_humidity_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    return _resp(_use_case(request).execute("humidity", time))


@router.get("/wind/grid", summary="WRF wind speed grid data")
def wrf_wind_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    """
    Returns wind speed (sqrt(U10² + V10²)) as a grid.
    Computed from U10 and V10 components — no separate wind endpoint needed.
    """
    import numpy as np
    from app.application.use_cases_grid import _to_float_list, _to_2d_list

    container = request.app.state.container
    u_grid = container.wrf_reader.read_variable("U10", time)
    v_grid = container.wrf_reader.read_variable("V10", time)
    speed  = np.sqrt(u_grid.values ** 2 + v_grid.values ** 2)

    result = GridDataResult(
        variable="wind",
        unit="m/s",
        time=time or "latest",
        lat_min=float(u_grid.lats.min()),
        lat_max=float(u_grid.lats.max()),
        lon_min=float(u_grid.lons.min()),
        lon_max=float(u_grid.lons.max()),
        lats=_to_float_list(
            u_grid.lats[:, 0] if u_grid.lats.ndim == 2 else u_grid.lats
        ),
        lons=_to_float_list(
            u_grid.lons[0, :] if u_grid.lons.ndim == 2 else u_grid.lons
        ),
        values=_to_2d_list(speed),
    )
    return _resp(result)


@router.get("/wind_direction/grid", summary="WRF wind direction grid data")
def wrf_wind_direction_grid(
    request: Request,
    time: Optional[str] = None,
) -> JSONResponse:
    """
    Returns meteorological wind direction (degrees FROM which wind blows)
    computed from U10 and V10 components.

    Convention:  0° = from North, 90° = from East, 180° = from South, etc.
    Formula:     direction = atan2(-U, -V) converted to 0–360°
    """
    import numpy as np
    from app.application.use_cases_grid import _to_float_list, _to_2d_list

    container = request.app.state.container
    u_grid = container.wrf_reader.read_variable("U10", time)
    v_grid = container.wrf_reader.read_variable("V10", time)

    # Meteorological direction: from which direction the wind blows
    direction = (np.degrees(np.arctan2(-u_grid.values, -v_grid.values)) + 360) % 360

    result = GridDataResult(
        variable="wind_direction",
        unit="°",
        time=time or "latest",
        lat_min=float(u_grid.lats.min()),
        lat_max=float(u_grid.lats.max()),
        lon_min=float(u_grid.lons.min()),
        lon_max=float(u_grid.lons.max()),
        lats=_to_float_list(
            u_grid.lats[:, 0] if u_grid.lats.ndim == 2 else u_grid.lats
        ),
        lons=_to_float_list(
            u_grid.lons[0, :] if u_grid.lons.ndim == 2 else u_grid.lons
        ),
        values=_to_2d_list(direction),
    )
    return _resp(result)
