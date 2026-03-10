FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    WRF_DIR=/wrf

WORKDIR /app

# Системные зависимости:
# - libeccodes-dev: GRIB (cfgrib/eccodes)
# - libfreetype6 + libpng: matplotlib PNG
# - tini: корректный PID 1 в контейнере (опционально, но полезно)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libeccodes-dev \
    libfreetype6 \
    libpng16-16 \
    tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]