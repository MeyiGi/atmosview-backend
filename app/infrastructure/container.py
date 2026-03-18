"""
infrastructure/container.py

Dependency-injection container.

Singletons (adapters, cache, use case instances) are created once at
application startup.  FastAPI dependencies in the presentation layer
call into this container rather than instantiating infrastructure objects
themselves.

This is intentionally simple — no third-party DI framework needed at this
scale.  If the project grows, the container can be replaced with
dependency-injector or punq without touching any other layer.
"""

from app.domain.entities import BoundingBox
from app.domain.interfaces import DataCache, WeatherDataReader, WeatherRenderer
from app.infrastructure.adapters.grib_reader import GribReaderAdapter
from app.infrastructure.adapters.rendering import MatplotlibRenderer
from app.infrastructure.adapters.wrf_reader import WrfReaderAdapter
from app.infrastructure.cache.in_memory_cache import InMemoryLRUCache
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.adapters.wrf_reader.strategies import register_all_strategies


class Container:
    """
    Holds application-lifetime singletons.
    Instantiated once in main.py and stored on app.state.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        # Shared cache — lives for the process lifetime
        self.cache: DataCache = InMemoryLRUCache(max_size=256)

        # Renderer — stateless, safe to share
        self.renderer: WeatherRenderer = MatplotlibRenderer()

        # GRIB readers — open the dataset once and cache on the instance
        self.temperature_reader: WeatherDataReader = GribReaderAdapter(settings.TEMPERATURE_GRIB)
        self.pressure_reader: WeatherDataReader = GribReaderAdapter(settings.PRESSURE_GRIB)
        self.precipitation_reader: WeatherDataReader = GribReaderAdapter(settings.PRECIPITATION_GRIB)
        self.wind_u_reader:       WeatherDataReader = GribReaderAdapter(settings.WIND_U_GRIB)
        self.wind_v_reader:       WeatherDataReader = GribReaderAdapter(settings.WIND_V_GRIB)
        self.humidity_reader: WeatherDataReader = GribReaderAdapter(settings.HUMIDITY_GRIB)

        # WRF reader
        register_all_strategies()
        self.wrf_reader = WrfReaderAdapter(settings.WRF_DIR)

        # Region bounding box
        self.bbox = BoundingBox(
            lat_min=settings.REGION_LAT_MIN,
            lat_max=settings.REGION_LAT_MAX,
            lon_min=settings.REGION_LON_MIN,
            lon_max=settings.REGION_LON_MAX,
        )

    # Reader look-up — maps variable name → reader instance
    # Used by the generic /weather/{variable} router.

    def get_reader_for_variable(self, variable: str) -> GribReaderAdapter:
        mapping = {
            "temperature": self.temperature_reader,
            "pressure": self.pressure_reader,
            "precipitation" : self.precipitation_reader,
            "wind_speed":    self.wind_u_reader,
            "wind_direction":self.wind_u_reader,
            "humidity" : self.humidity_reader
        }
        reader = mapping.get(variable)
        if reader is None:
            from app.domain.exceptions import VariableNotFoundError
            raise VariableNotFoundError(f"No reader configured for variable '{variable}'")
        return reader


def build_container() -> Container:
    return Container(settings=get_settings())
