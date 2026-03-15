"""
presentation/routers/wrf.py

WRF model output endpoints. Each route validates HTTP input, builds a
WrfRenderQuery DTO, and delegates entirely to the use case.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response

from app.application.dtos import RenderWindQuery, WrfRenderQuery
from app.application.use_cases import GetWrfMetaUseCase, RenderWrfMapUseCase, RenderWrfWindUseCase
from app.presentation.dependencies import get_wrf_meta_use_case, render_wrf_map_use_case, render_wrf_wind_use_case

router = APIRouter(prefix="/wrf", tags=["WRF"])

_TIME_DESCRIPTION = (
    "WRF filename timestamp. "
    "Examples: 2026-03-12_120000 or 2026-03-12_12:00:00. "
    "Omit to use the latest available file."
)


@router.get(
    "/temperature",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF 2-metre temperature map",
)
def wrf_temperature(
    time: str | None = Query(None, description=_TIME_DESCRIPTION),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(wrf_variable="T2", display_name="Temperature", unit_label="°C", time=time)
    return Response(content=use_case.execute(query), media_type="image/png")


@router.get(
    "/pressure",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF surface pressure map",
)
def wrf_pressure(
    time: str | None = Query(None, description=_TIME_DESCRIPTION),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(wrf_variable="PSFC", display_name="Pressure", unit_label="hPa", time=time)
    return Response(content=use_case.execute(query), media_type="image/png")


@router.get(
    "/precipitation",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF accumulated precipitation map",
    description=(
        "Returns a PNG map of total accumulated precipitation (RAINC + RAINNC) "
        "from WRF model output for the given timestep."
    ),
)
def wrf_precipitation(
    time: str | None = Query(None, description=_TIME_DESCRIPTION),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(wrf_variable="PRECIPITATION", display_name="Precipitation", unit_label="mm", time=time)
    return Response(content=use_case.execute(query), media_type="image/png")

@router.get(
    "/wind",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF wind map",
    description="Wind speed as background color, wind direction as arrows. Uses U10 and V10 components.",
)
def wrf_wind(
    time: str | None = Query(None, description=_TIME_DESCRIPTION),
    use_case: RenderWrfWindUseCase = Depends(render_wrf_wind_use_case),
) -> Response:
    return Response(content=use_case.execute(RenderWindQuery(time=time)), media_type="image/png")

@router.get(
    "/meta",
    summary="WRF domain metadata",
    description="Returns the spatial bounds and list of available output times.",
)
def wrf_meta(
    use_case: GetWrfMetaUseCase = Depends(get_wrf_meta_use_case),
) -> JSONResponse:
    return JSONResponse(content=use_case.execute())