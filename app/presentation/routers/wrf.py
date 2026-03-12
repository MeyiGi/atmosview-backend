"""
presentation/routers/wrf.py

WRF model output endpoints.

WRF routes now follow the same architectural contract as the GRIB routes:
routers delegate to use cases, use cases delegate to adapters.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response

from app.application.dtos import WrfRenderQuery
from app.application.use_cases import GetWrfMetaUseCase, RenderWrfMapUseCase
from app.presentation.dependencies import get_wrf_meta_use_case, render_wrf_map_use_case

router = APIRouter(prefix="/wrf", tags=["WRF"])

@router.get(
    "/temperature",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF 2-metre temperature map",
)
def wrf_temperature(
    time: str | None = Query(
        None,
        description="WRF time. Examples: 2026-03-12_120000 or 2026-03-12_12:00:00",
    ),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(
        wrf_variable="T2",
        display_name="Temperature",
        unit_label="°C",
        time=time,
    )
    return Response(content=use_case.execute(query), media_type="image/png")


@router.get(
    "/pressure",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF surface pressure map",
)
def wrf_pressure(
    time: str | None = Query(None, description="WRF filename timestamp"),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(
        wrf_variable="PSFC",
        display_name="Pressure",
        unit_label="hPa",
        time=time,
    )
    return Response(content=use_case.execute(query), media_type="image/png")


@router.get(
    "/meta",
    summary="WRF domain metadata",
    description="Returns the spatial bounds and list of available output times.",
)
def wrf_meta(
    use_case: GetWrfMetaUseCase = Depends(get_wrf_meta_use_case),
) -> JSONResponse:
    return JSONResponse(content=use_case.execute())
