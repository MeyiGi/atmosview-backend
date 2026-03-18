# Central Asia Weather API

REST API for meteorological data visualisation. Reads **GRIB** and **WRF** netCDF output files, clips data to the Central Asia region, and returns rendered **PNG maps**.

Built with FastAPI, xarray, cfgrib, and Matplotlib. Follows Clean Architecture — domain logic has zero framework dependencies.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Running with Docker](#running-with-docker)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Caching](#caching)
- [Request Logging](#request-logging)
- [Adding a New Variable](#adding-a-new-variable)
- [Data Sources](#data-sources)

---

## Quick Start

**Requirements:** Python 3.13+

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd central-asia-weather-api

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place your data files
mkdir -p data/wrf
# Copy wrfout_d01_* files into data/wrf/
# Copy *.grib files into data/

# 5. Start the server
uvicorn app.main:app --reload
```

Interactive API docs → `http://127.0.0.1:8000/`

---

## Running with Docker

### docker-compose (recommended)

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WRF_DIR=/wrf
    volumes:
      - ./data:/app/data               # GRIB files + SQLite database
      - /your/wrf_output:/wrf          # WRF wrfout files (read-only mount)
    restart: unless-stopped
```

```bash
docker compose up --build
```

### What the Dockerfile does

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \      # headless matplotlib — no display needed
    WRF_DIR=/wrf

WORKDIR /app

# System packages required:
#   libeccodes-dev  — GRIB decoding (cfgrib/eccodes)
#   libfreetype6    — font rendering for matplotlib
#   libpng16-16     — PNG output for matplotlib
#   tini            — correct PID 1 signal handling in containers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeccodes-dev libfreetype6 libpng16-16 tini ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
```

**Key points:**
- `MPLBACKEND=Agg` must be set so Matplotlib never tries to open a display window inside the container.
- `tini` is used as PID 1 so SIGTERM is forwarded correctly and zombie processes are reaped.
- `data/` is volume-mounted at runtime so GRIB files and the SQLite database survive container restarts.
- WRF files are typically large — mount them from the host rather than copying them into the image.

### Volume mapping guide

| Host path | Container path | Purpose |
|---|---|---|
| `./data` | `/app/data` | GRIB files, SQLite DB |
| `/your/wrf_output` | `/wrf` (or `WRF_DIR`) | WRF `wrfout_d01_*` files |

---

## Project Structure

```
central-asia-weather-api/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── data/                               # Runtime data (not committed to git)
│   ├── temperature.grib
│   ├── pressure.grib
│   ├── precipitation.grib
│   ├── wind_u.grib
│   ├── wind_v.grib
│   ├── weather.db                      # SQLite request log (auto-created)
│   └── wrf/
│       ├── wrfout_d01_2026-03-12_120000
│       └── wrfout_d01_2026-03-13_000000
│
└── app/
    ├── main.py                         # App entrypoint, lifespan, router registration
    │
    ├── domain/                         # ── Inner layer: no framework deps ──
    │   ├── entities.py                 # WeatherGrid, VariableSpec, BoundingBox, RenderRequest, WrfMeta
    │   ├── interfaces.py               # Abstract ports: WeatherDataReader, WrfDataReader, WeatherRenderer, DataCache, RequestLogRepository
    │   └── exceptions.py              # DomainError, DataSourceError, TimeNotFoundError, VariableNotFoundError, UnsupportedRenderMetricError
    │
    ├── application/                    # ── Use cases and DTOs ──
    │   ├── use_cases.py                # RenderWeatherMapUseCase, RenderWrfMapUseCase, RenderWrfWindUseCase, GetWrfMetaUseCase, GetRequestLogsUseCase
    │   ├── dtos.py                     # RenderMapQuery, WrfRenderQuery, RenderWindQuery, RequestLogEntry
    │   └── variable_specs/             # Builder pattern for variable metadata
    │       ├── builder.py              # Abstract VariableSpecBuilder
    │       ├── director.py             # VariableSpecDirector — orchestrates builder steps
    │       ├── registry.py             # Maps variable name → builder class + get_variable_spec()
    │       └── implementations/        # One file per variable
    │           ├── temperature_builder.py
    │           ├── pressure_builder.py
    │           ├── precipitation_builder.py
    │           ├── wind_speed_builder.py
    │           ├── wind_direction_builder.py
    │           └── humidity.py
    │
    ├── infrastructure/                 # ── Outer layer: all framework/library code ──
    │   ├── config/
    │   │   └── settings.py             # Pydantic BaseSettings — reads .env
    │   ├── container.py                # DI container — creates and holds all singletons
    │   ├── cache/
    │   │   └── in_memory_cache.py      # Thread-safe LRU cache (OrderedDict, max 256 entries)
    │   ├── persistence/
    │   │   ├── database.py             # SQLAlchemy engine + session factory
    │   │   ├── models/
    │   │   │   └── request_log.py      # RequestLogOrm SQLAlchemy model
    │   │   └── repositories/
    │   │       └── log_repository.py   # SqlAlchemyLogRepository
    │   └── adapters/
    │       ├── grib_reader/            # Reads GRIB files via cfgrib + xarray
    │       │   ├── adapter.py          # GribReaderAdapter (implements WeatherDataReader)
    │       │   ├── bbox_clipper.py     # Clips DataArray to bounding box
    │       │   └── time_selector.py    # Selects time slice from dataset
    │       ├── wrf_reader/             # Reads WRF netCDF output files
    │       │   ├── adapter.py          # WrfReaderAdapter (implements WrfDataReader)
    │       │   ├── registry.py         # Maps WRF key → strategy + @register_strategy decorator
    │       │   ├── helpers.py          # read_single() — safe variable extraction
    │       │   ├── file_locator.py     # Discovers and resolves wrfout files by timestamp
    │       │   ├── time_parser.py      # Parses WRF filename timestamps
    │       │   ├── coord_extractor.py  # Extracts lat/lon grids from WRF dataset
    │       │   └── strategies/         # One strategy per WRF variable
    │       │       ├── __init__.py     # register_all_strategies() — imports all strategies
    │       │       ├── base.py         # Abstract VirtualVariableStrategy
    │       │       ├── temperature.py  # T2 → K
    │       │       ├── pressure.py     # PSFC → Pa
    │       │       ├── precipitation.py # RAINC + RAINNC → mm
    │       │       ├── wind_speed.py   # U10, V10 → m/s
    │       │       ├── wind_direction.py
    │       │       └── humidity.py     # Q2 → kg/kg
    │       ├── rendering/              # Matplotlib PNG renderer
    │       │   ├── adapter.py          # MatplotlibRenderer (implements WeatherRenderer)
    │       │   ├── registry.py         # Maps metric name → RenderStrategy instance
    │       │   ├── specs.py            # ScalarRenderSpec dataclass + transform functions
    │       │   ├── helpers.py          # to_2d_coords() grid helper
    │       │   └── strategies/
    │       │       ├── base.py         # Abstract RenderStrategy
    │       │       ├── scalar.py       # ScalarMetricStrategy — contourf plot
    │       │       └── wind.py         # WindStrategy — speed field + direction arrows
    │       └── dataset_loader/
    │           ├── base.py             # Abstract DatasetLoader with _validate + _open
    │           ├── grib.py             # GridDatasetLoader (cfgrib engine)
    │           └── wrf.py              # WrfDatasetLoader (xarray.open_dataset)
    │
    └── presentation/                   # ── FastAPI layer ──
        ├── dependencies.py             # FastAPI Depends factories — wires use cases from container
        ├── schemas.py                  # Pydantic request validation schemas
        ├── exception_handlers.py       # Maps domain exceptions → HTTP status codes
        └── routers/
            ├── weather.py              # GET /weather/{variable} — generic GRIB-backed route
            ├── wrf.py                  # GET /wrf/* — WRF-backed routes
            └── logs.py                 # GET /logs
```

---

## Architecture Overview

The project follows **Clean Architecture**. Dependencies only point inward — infrastructure depends on application, application depends on domain. Domain has no external dependencies at all.

```
┌─────────────────────────────────────────────────┐
│              Presentation (FastAPI)              │
│         routers · dependencies · schemas         │
└───────────────────────┬─────────────────────────┘
                        │ calls
┌───────────────────────▼─────────────────────────┐
│              Application (Use Cases)             │
│          use_cases · dtos · variable_specs        │
└───────────────────────┬─────────────────────────┘
                        │ depends on interfaces from
┌───────────────────────▼─────────────────────────┐
│                   Domain                         │
│         entities · interfaces · exceptions        │
└───────────────────────▲─────────────────────────┘
                        │ implements
┌───────────────────────┴─────────────────────────┐
│           Infrastructure (Adapters)              │
│  grib_reader · wrf_reader · rendering · cache    │
└─────────────────────────────────────────────────┘
```

### Request flow example — `GET /wrf/humidity?time=2026-03-12_120000`

```
FastAPI router (wrf.py)
  → builds WrfRenderQuery(metric="humidity", wrf_variable="HUMIDITY", time=...)
  → calls RenderWrfMapUseCase.execute(query)

RenderWrfMapUseCase
  → calls WrfReaderAdapter.read_variable("HUMIDITY", "2026-03-12_120000")

WrfReaderAdapter
  → WrfFileLocator resolves the wrfout file by timestamp
  → WrfDatasetLoader opens the netCDF file with xarray
  → looks up "HUMIDITY" in strategy registry → HumidityStrategy
  → HumidityStrategy.compute() reads Q2 field via read_single()
  → returns WeatherGrid(lats, lons, values, variable, time)

RenderWrfMapUseCase
  → calls MatplotlibRenderer.render(RenderRequest(metric="humidity", grids={"main": grid}))

MatplotlibRenderer
  → looks up "humidity" in rendering registry → ScalarMetricStrategy(YlGnBu)
  → ScalarMetricStrategy.render() produces a contourf PNG figure
  → returns PNG bytes

FastAPI router
  → returns Response(content=png, media_type="image/png")
```

### Startup sequence (`main.py` lifespan)

```
1. build_container()          — instantiates all singletons (readers, renderer, cache)
2. register_all_strategies()  — fires @register_strategy decorators for all WRF variables
3. Base.metadata.create_all() — creates SQLite tables if they don't exist
4. yield                      — server accepts requests
```

---

## Configuration

All settings live in `app/infrastructure/config/settings.py` and are read from environment variables or a `.env` file via Pydantic `BaseSettings`.

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `./data` | Root directory for GRIB files and SQLite DB |
| `WRF_DIR` | `./data/wrf` | Directory containing `wrfout_d01_*` files |
| `REGION_LAT_MIN` | `35.0` | Southern boundary of the clip region |
| `REGION_LAT_MAX` | `55.0` | Northern boundary of the clip region |
| `REGION_LON_MIN` | `50.0` | Western boundary of the clip region |
| `REGION_LON_MAX` | `90.0` | Eastern boundary of the clip region |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`) |
| `SQLITE_FILENAME` | `weather.db` | SQLite filename inside `DATA_DIR` |
| `PROJECT_NAME` | `Weather API` | Title shown in OpenAPI docs |

**Example `.env` file:**

```env
DATA_DIR=/app/data
WRF_DIR=/wrf
REGION_LAT_MIN=35.0
REGION_LAT_MAX=55.0
REGION_LON_MIN=50.0
REGION_LON_MAX=90.0
LOG_LEVEL=INFO
```

---

## API Reference

### WRF endpoints

All WRF endpoints read from `WRF_DIR` and accept an optional `?time=` parameter. When `time` is omitted, the **most recent** `wrfout` file is used.

**Time format:** `YYYY-MM-DD_HHMMSS` or `YYYY-MM-DD_HH:MM:SS`
**Example:** `?time=2026-03-12_120000`

| Method | Path | WRF field | Unit | Description |
|---|---|---|---|---|
| GET | `/wrf/temperature` | `T2` | K | 2-metre air temperature |
| GET | `/wrf/pressure` | `PSFC` | Pa | Surface pressure |
| GET | `/wrf/precipitation` | `RAINC + RAINNC` | mm | Accumulated precipitation |
| GET | `/wrf/wind` | `U10`, `V10` | m/s + degrees | Wind speed (color) + direction (arrows) |
| GET | `/wrf/humidity` | `Q2` | kg/kg | 2-metre specific humidity |
| GET | `/wrf/meta` | — | — | Domain bounds + available timestamps (JSON) |

### GRIB endpoints

Reads from pre-processed GRIB files in `DATA_DIR`.

**Time format:** ISO 8601 — `YYYY-MM-DDTHH:MM`
**Example:** `?time=2025-01-29T00:00`

| Method | Path | Description |
|---|---|---|
| GET | `/weather/{variable}` | Returns PNG for any registered variable. Available: `temperature`, `pressure`, `precipitation`, `wind_speed`, `wind_direction` |

### Other

| Method | Path | Description |
|---|---|---|
| GET | `/logs?limit=100` | Recent request audit log (JSON) |
| GET | `/` | Interactive OpenAPI documentation (Swagger UI) |

### Response types

| Scenario | Status | Body |
|---|---|---|
| Success | `200` | `image/png` binary |
| Variable not found | `404` | `{"detail": "..."}` |
| Timestamp not found | `404` | `{"detail": "..."}` |
| Data source error | `500` | `{"detail": "..."}` |

---

## Error Handling

Domain exceptions are mapped to HTTP responses in `presentation/exception_handlers.py`:

| Exception | HTTP status | When it's raised |
|---|---|---|
| `VariableNotFoundError` | `404` | Variable name not in registry, or WRF field missing from file |
| `TimeNotFoundError` | `404` | Requested timestamp not found in GRIB dataset |
| `DataSourceError` | `500` | File not found, cannot open, or no data variables in file |
| `UnsupportedRenderMetricError` | `500` | Metric not registered in rendering registry |

---

## Caching

Rendered PNG bytes are cached in memory using a **thread-safe LRU cache** (`InMemoryLRUCache`, max 256 entries). Cache keys are `"{variable}:{iso_timestamp}"`.

- Cache hits skip both the file read and the rendering step entirely.
- The cache lives for the process lifetime — it is cleared on container restart.
- To swap for Redis, implement the `DataCache` interface and inject it in `container.py`.

---

## Request Logging

Every API request is written to a SQLite table (`request_logs`) via `SqlAlchemyLogRepository`. The table is auto-created on startup.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-increment primary key |
| `endpoint` | TEXT | Route path e.g. `/wrf/humidity` |
| `requested_time` | TEXT | The time parameter from the request |
| `status` | TEXT | `"success"` or `"error"` |
| `error_message` | TEXT | Error detail if status is `"error"` |
| `created_at` | DATETIME | UTC timestamp of the request |

Log writes are fire-and-forget — a persistence failure never affects the HTTP response.

Retrieve recent logs:
```bash
curl http://127.0.0.1:8000/logs?limit=50
```

---

## Adding a New Variable

This example adds `snow_depth`. Follow all 6 steps in order.

---

### Step 1 — WRF reader strategy

Create `app/infrastructure/adapters/wrf_reader/strategies/snow_depth.py`:

```python
from pathlib import Path
import numpy as np
import xarray as xr

from app.infrastructure.adapters.wrf_reader.registry import register_strategy
from app.infrastructure.adapters.wrf_reader.helpers import read_single
from .base import VirtualVariableStrategy


@register_strategy("SNOW_DEPTH")
class SnowDepthStrategy(VirtualVariableStrategy):
    """Snow depth in metres (SNOWH)."""
    def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
        return read_single(ds, "SNOWH", path)
```

The key passed to `@register_strategy` is what you use as `wrf_variable` in the router (Step 6). The WRF field name itself (`SNOWH`) is what you pass to `read_single` — check your WRF output file for the exact name.

For **derived variables** that combine multiple fields (like precipitation uses `RAINC + RAINNC`):

```python
def compute(self, ds: xr.Dataset, path: Path) -> np.ndarray:
    a = read_single(ds, "FIELD_A", path)
    b = read_single(ds, "FIELD_B", path)
    return a + b
```

---

### Step 2 — Register the strategy

Open `app/infrastructure/adapters/wrf_reader/strategies/__init__.py` and add one import inside `register_all_strategies()`:

```python
def register_all_strategies() -> None:
    from . import precipitation
    from . import wind_speed
    from . import wind_direction
    from . import temperature
    from . import pressure
    from . import humidity
    from . import snow_depth    # ← add this
```

---

### Step 3 — Variable spec builder

Create `app/application/variable_specs/implementations/snow_depth_builder.py`:

```python
from app.application.variable_specs.builder import VariableSpecBuilder


class SnowDepthBuilder(VariableSpecBuilder):
    def build_name(self) -> None:
        self._name = "snow_depth"

    def build_colormap(self) -> None:
        self._colormap = "Blues"

    def build_unit_label(self) -> None:
        self._unit_label = "Snow Depth (m)"
```

The `name` must be identical to the dict key added in Step 4 and the rendering registry key in Step 5.

**Colormap reference:**

| Variable type | Colormap |
|---|---|
| Temperature | `RdYlBu_r` |
| Humidity / precipitation / snow | `Blues` or `YlGnBu` |
| Pressure / geopotential | `viridis` |
| Wind speed | `YlOrRd` |
| General scalar | `plasma`, `magma`, `coolwarm` |

---

### Step 4 — Variable spec registry

Open `app/application/variable_specs/registry.py`:

```python
from app.application.variable_specs.implementations.snow_depth_builder import SnowDepthBuilder

_BUILDERS: dict[str, type[VariableSpecBuilder]] = {
    "temperature":    TemperatureBuilder,
    "pressure":       PressureBuilder,
    "precipitation":  PrecipitationBuilder,
    "wind_speed":     WindSpeedBuilder,
    "wind_direction": WindDirectionBuilder,
    "humidity":       HumidityBuilder,
    "snow_depth":     SnowDepthBuilder,    # ← add this
}
```

---

### Step 5 — Rendering registry

Open `app/infrastructure/adapters/rendering/registry.py` and add an entry to `_RENDERER`:

```python
"snow_depth": ScalarMetricStrategy(
    ScalarRenderSpec(
        title="Snow Depth",
        unit_label="m",
        cmap="Blues",
        # transform defaults to identity — values already in metres
    )
),
```

**Available transforms** (defined in `rendering/specs.py`):

| Function | Use when |
|---|---|
| `identity` | Values already in the display unit (default) |
| `kelvin_to_celsius` | Temperature stored in Kelvin (T2) |
| `pascal_to_hpa` | Pressure stored in Pascals (PSFC) |

To add a custom transform, define a `(np.ndarray) -> np.ndarray` function in `specs.py` and reference it via `ScalarRenderSpec(transform=your_fn)`.

For **two-component variables** (like wind), create a new strategy class in `rendering/strategies/` following the `WindStrategy` pattern, then register the instance directly:

```python
"my_vector": MyVectorStrategy(),
```

---

### Step 6 — Router endpoint

Open `app/presentation/routers/wrf.py` and add:

```python
@router.get(
    "/snow_depth",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {}, 500: {}},
    summary="WRF snow depth map",
    description="Returns a PNG map of snow depth (SNOWH) in metres from WRF output.",
)
def wrf_snow_depth(
    time: str | None = Query(None, description=_TIME_DESCRIPTION),
    use_case: RenderWrfMapUseCase = Depends(render_wrf_map_use_case),
) -> Response:
    query = WrfRenderQuery(metric="snow_depth", wrf_variable="SNOW_DEPTH", time=time)
    return Response(content=use_case.execute(query), media_type="image/png")
```

`metric` must match the rendering registry key (Step 5).
`wrf_variable` must match the `@register_strategy` key (Step 1).

---

### Full checklist

| # | File | Action |
|---|---|---|
| 1 | `wrf_reader/strategies/snow_depth.py` | **Create** — reads the raw WRF field |
| 2 | `wrf_reader/strategies/__init__.py` | **Edit** — add import in `register_all_strategies()` |
| 3 | `variable_specs/implementations/snow_depth_builder.py` | **Create** — name, colormap, unit label |
| 4 | `variable_specs/registry.py` | **Edit** — add to `_BUILDERS` dict |
| 5 | `rendering/registry.py` | **Edit** — add to `_RENDERER` dict |
| 6 | `presentation/routers/wrf.py` | **Edit** — add GET endpoint |

---

## Data Sources

### WRF output files

Expected naming convention (standard WRF output):

```
data/wrf/wrfout_d01_2026-03-12_120000
data/wrf/wrfout_d01_2026-03-12_180000
data/wrf/wrfout_d01_2026-03-13_000000
```

- The API discovers all `wrfout_d01_*` files in `WRF_DIR` automatically.
- Files are selected by matching the timestamp token in the filename.
- When no `?time=` is given, the file with the **latest** timestamp is used.
- Files are opened with `xarray.open_dataset` (netCDF4).

### GRIB files

Expected location and naming (one variable per file):

```
data/temperature.grib
data/pressure.grib
data/precipitation.grib
data/wind_u.grib
data/wind_v.grib
```

- Files are opened via the `cfgrib` engine through xarray.
- The reader uses the **first data variable** found in the file — the internal variable name does not need to match the filename.
- File paths are defined as `@property` methods in `settings.py`. To change a path, update the property there.
- GRIB files are validated at application startup — the server will **not start** if a configured GRIB file is missing. If a variable has no GRIB file (e.g. humidity only exists in WRF), do not add a `GribReaderAdapter` for it in `container.py`.