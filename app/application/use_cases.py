"""
application/use_cases.py

Use cases (interactors) — the heart of the application layer.

Rules:
  * Depend only on domain interfaces and DTOs.
  * Zero framework imports (no FastAPI, no SQLAlchemy, no xarray).
  * Orchestrate: read → render → log.  Nothing else.
  * Logging is fire-and-forget; it must not block or propagate errors.
"""

import logging
from datetime import datetime

from app.application.dtos import RenderMapQuery, RenderWindQuery, RequestLogEntry, WrfRenderQuery
from app.domain.entities import BoundingBox, VariableSpec
from app.domain.interfaces import (
    DataCache,
    RequestLogRepository,
    WeatherDataReader,
    WeatherRenderer,
    WrfDataReader,
)
from app.application.variable_specs.registry import get_variable_spec

logger = logging.getLogger(__name__)



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cache_key(variable: str, time: datetime) -> str:
    return f"{variable}:{time.isoformat()}"


def _safe_log(
    repo: RequestLogRepository,
    endpoint: str,
    time_str: str,
    status: str,
    error: str | None = None,
) -> None:
    """Write a request log entry; swallow any persistence error so it never
    impacts the response path."""
    try:
        repo.save(endpoint, time_str, status, error)
    except Exception:
        logger.exception("Failed to write request log for %s", endpoint)


# ---------------------------------------------------------------------------
# Use case: render a GRIB-backed weather variable map
# ---------------------------------------------------------------------------


class RenderWeatherMapUseCase:
    """
    Renders a PNG map for a registered weather variable from the primary
    GRIB data source.

    Depends on:
        reader   — WeatherDataReader  (GRIB adapter injected)
        renderer — WeatherRenderer    (matplotlib adapter injected)
        log_repo — RequestLogRepository
        cache    — DataCache
        bbox     — BoundingBox        (from settings, injected once)
    """

    def __init__(
        self,
        reader: WeatherDataReader,
        renderer: WeatherRenderer,
        log_repo: RequestLogRepository,
        cache: DataCache,
        bbox: BoundingBox,
    ) -> None:
        self._reader = reader
        self._renderer = renderer
        self._log_repo = log_repo
        self._cache = cache
        self._bbox = bbox

    def execute(self, query: RenderMapQuery) -> bytes:
        spec: VariableSpec = get_variable_spec(query.variable)  # raises VariableNotFoundError
        time_str = query.time.isoformat()
        cache_key = _cache_key(spec.name, query.time)

        cached = self._cache.get(cache_key)
        if isinstance(cached, bytes):
            _safe_log(self._log_repo, f"/{spec.name}", time_str, "success")
            return cached

        grid = self._reader.read(spec.name, query.time, self._bbox)
        png = self._renderer.render_png(grid)

        self._cache.set(cache_key, png)
        _safe_log(self._log_repo, f"/{spec.name}", time_str, "success")
        return png


# ---------------------------------------------------------------------------
# Use case: render a WRF variable map
# ---------------------------------------------------------------------------


class RenderWrfMapUseCase:
    """
    Renders a PNG map from WRF model output.

    The WRF reader handles file discovery (latest vs. specific timestamp),
    so the use case stays thin.
    """

    def __init__(
        self,
        wrf_reader: WrfDataReader,
        renderer: WeatherRenderer,
        log_repo: RequestLogRepository,
    ) -> None:
        self._wrf_reader = wrf_reader
        self._renderer = renderer
        self._log_repo = log_repo

    def execute(self, query: WrfRenderQuery) -> bytes:
        endpoint = f"/wrf/{query.display_name.lower()}"
        time_str = query.time or "latest"

        grid = self._wrf_reader.read_variable(query.wrf_variable, query.time)
        # Override spec labels from the query so the renderer can use them
        png = self._renderer.render_png(grid)

        _safe_log(self._log_repo, endpoint, time_str, "success")
        return png


# ---------------------------------------------------------------------------
# Use case: retrieve WRF domain metadata
# ---------------------------------------------------------------------------


class GetWrfMetaUseCase:
    def __init__(self, wrf_reader: WrfDataReader) -> None:
        self._wrf_reader = wrf_reader

    def execute(self) -> dict:
        meta = self._wrf_reader.get_meta()
        return {
            "bounds": list(meta.bounds),
            "available_times": meta.available_times,
        }


# ---------------------------------------------------------------------------
# Use case: fetch request logs
# ---------------------------------------------------------------------------


class GetRequestLogsUseCase:
    def __init__(self, log_repo: RequestLogRepository) -> None:
        self._log_repo = log_repo

    def execute(self, limit: int) -> list[RequestLogEntry]:
        rows = self._log_repo.get_recent(limit)
        return [RequestLogEntry(**row) for row in rows]

# ---------------------------------------------------------------------------
# Use case: show wind information
# ---------------------------------------------------------------------------

class RenderWrfWindUseCase:
    """
    Renders a single PNG with wind speed as background
    and wind direction as arrows. Reads U10 and V10 directly
    so the renderer gets both components.
    """

    def __init__(
        self,
        wrf_reader: WrfDataReader,
        renderer: WeatherRenderer,
        log_repo: RequestLogRepository,
    ) -> None:
        self._wrf_reader = wrf_reader
        self._renderer = renderer
        self._log_repo = log_repo

    def execute(self, query: RenderWindQuery) -> bytes:
        u_grid = self._wrf_reader.read_variable("U10", query.time)
        v_grid = self._wrf_reader.read_variable("V10", query.time)
        png = self._renderer.render_wind_png(u_grid, v_grid)
        _safe_log(self._log_repo, "/wrf/wind", query.time or "latest", "success")
        return png