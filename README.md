# Weather API

A REST API built with FastAPI that reads meteorological data from GRIB files and returns weather map visualizations as PNG images. Covers the Central Asia region (35–55°N, 50–90°E).

---

## Purpose

This service exposes temperature and atmospheric pressure fields from GRIB2 files as on-demand map images. Each request returns a filled-contour PNG rendered with Matplotlib. All requests are logged to a local SQLite database for monitoring and debugging.

---

## Installation

### Option A — Docker (recommended)

Make sure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) installed.

```bash
git clone https://github.com/MeyiGi/central-asia-weather-api.git
cd backend
docker compose up --build
```

The API will be available at `http://localhost:8000`.

---

### Option B — Local (Python)

**Requirements:** Python 3.11+, and the `eccodes` C library (required by cfgrib).

**1. Install eccodes (system dependency)**

```bash
# Ubuntu / Debian
sudo apt-get install libeccodes-dev

# macOS
brew install eccodes
```

**2. Create a virtual environment and install Python packages**

```bash
python -m venv venv
source venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**3. Place GRIB data files**

Make sure the following files are present in the `data/` directory:

```
data/
├── temperature.grib
└── pressure.grib
```

**4. Start the server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Running the API

Once started, the interactive Swagger UI is available at:

```
http://localhost:8000
```

This lets you explore and test all endpoints directly in the browser.

---

## API Endpoints

### `GET /temperature`

Returns a PNG map of near-surface temperature (in Kelvin) over Central Asia at the given time.

| Parameter | Type   | Required | Description                                    |
|-----------|--------|----------|------------------------------------------------|
| `time`    | string | Yes      | ISO 8601 datetime, e.g. `2025-01-29T00:00`    |

**Responses:**

| Status | Description                                      |
|--------|--------------------------------------------------|
| `200`  | PNG image (`image/png`)                          |
| `404`  | No data found for the requested time             |
| `422`  | Invalid or missing `time` parameter              |
| `500`  | Failed to read the GRIB file                     |

---

### `GET /pressure`

Returns a PNG map of surface pressure (in Pascals) over Central Asia at the given time. Identical behaviour to `/temperature`.

| Parameter | Type   | Required | Description                                    |
|-----------|--------|----------|------------------------------------------------|
| `time`    | string | Yes      | ISO 8601 datetime, e.g. `2025-01-29T00:00`    |

---

### `GET /logs`

Returns recent API request logs from the SQLite database.

| Parameter | Type    | Required | Default | Description                        |
|-----------|---------|----------|---------|------------------------------------|
| `limit`   | integer | No       | 50      | Maximum number of entries to return |

**Example response:**

```json
[
  {
    "id": 1,
    "endpoint": "/temperature",
    "requested_time": "2025-01-29T00:00",
    "status": "success",
    "error_message": null,
    "created_at": "2025-01-29T10:34:21"
  }
]
```

---

## Example Requests

**Get a temperature map and save it as a PNG file:**

```bash
curl "http://localhost:8000/temperature?time=2025-01-29T00:00" --output temperature.png
```

**Get a pressure map:**

```bash
curl "http://localhost:8000/pressure?time=2025-01-29T06:00" --output pressure.png
```

**Fetch the last 10 request logs:**

```bash
curl "http://localhost:8000/logs?limit=10"
```

**Using Python (requests library):**

```python
import requests

# Download a temperature map
response = requests.get(
    "http://localhost:8000/temperature",
    params={"time": "2025-01-29T00:00"}
)

if response.status_code == 200:
    with open("temperature.png", "wb") as f:
        f.write(response.content)
    print("Saved temperature.png")
else:
    print(f"Error {response.status_code}: {response.json()}")
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, middleware, lifespan
│   ├── core/
│   │   ├── config.py            # Settings (paths, region bbox, DB URL)
│   │   ├── database.py          # SQLAlchemy engine & session factory
│   │   └── exceptions.py        # Custom exception types
│   ├── routes/
│   │   └── routes.py            # HTTP route handlers
│   ├── services/
│   │   ├── weather_service.py   # Orchestrates read → clip → render
│   │   ├── grib_reader.py       # Parses GRIB files via cfgrib/xarray
│   │   ├── base_reader.py       # Abstract reader interface
│   │   └── visualization.py     # Renders PNG maps with Matplotlib
│   ├── repository/
│   │   └── log_repository.py    # Database access for request logs
│   ├── models/
│   │   └── request_log.py       # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── weather.py           # Pydantic schemas
│   └── utils/                   # Geo, time, file, and response helpers
├── data/                        # GRIB files and SQLite DB (volume-mounted)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Configuration

The following settings can be overridden via environment variables or a `.env` file:

| Variable            | Default              | Description                          |
|---------------------|----------------------|--------------------------------------|
| `PROJECT_NAME`      | `Weather API`        | Title shown in Swagger UI            |
| `DATA_DIR`          | `./data`             | Directory for GRIB files and DB      |
| `TEMPERATURE_GRIB`  | `data/temperature.grib` | Path to temperature GRIB file     |
| `PRESSURE_GRIB`     | `data/pressure.grib` | Path to pressure GRIB file           |
| `SQLITE_FILENAME`   | `weather.db`         | SQLite database filename             |
| `REGION_LAT_MIN/MAX`| `35.0` / `55.0`      | Latitude bounds of the output region |
| `REGION_LON_MIN/MAX`| `50.0` / `90.0`      | Longitude bounds of the output region |