from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Weather API"
    LOG_LEVEL: str = "INFO"

    DATA_DIR: Path = BASE_DIR / "data"

    @property
    def TEMPERATURE_GRIB(self) -> Path:
        return self.DATA_DIR / "temperature.grib"

    @property
    def PRESSURE_GRIB(self) -> Path:
        return self.DATA_DIR / "pressure.grib"
    
    @property
    def PRECIPITATION_GRIB(self) -> Path:
        return self.DATA_DIR / "precipitation.grib"

    WRF_DIR: Path = BASE_DIR / "data" / "wrf"

    SQLITE_FILENAME: str = "weather.db"

    @property
    def DATABASE_URL(self) -> str:
        db_path = self.DATA_DIR / self.SQLITE_FILENAME
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"
    
    @property
    def WIND_U_GRIB(self) -> Path:
        return self.DATA_DIR / "wind_u.grib"

    @property
    def WIND_V_GRIB(self) -> Path:
        return self.DATA_DIR / "wind_v.grib"

    REGION_LAT_MIN: float = 35.0
    REGION_LAT_MAX: float = 55.0
    REGION_LON_MIN: float = 50.0
    REGION_LON_MAX: float = 90.0

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()