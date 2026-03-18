from app.infrastructure.adapters.rendering.strategies.base import RenderStrategy 
from app.infrastructure.adapters.rendering.strategies.scalar import ScalarMetricStrategy
from app.infrastructure.adapters.rendering.specs import kelvin_to_celsius, ScalarRenderSpec, pascal_to_hpa
from app.infrastructure.adapters.rendering.strategies.wind import WindStrategy
from app.domain.exceptions import UnsupportedRenderMetricError

_RENDERER = {
    "temperature" : ScalarMetricStrategy(
        ScalarRenderSpec(
            title="Temperature",
            unit_label="°C",
            cmap="RdYlBu_r",
            transform=kelvin_to_celsius,
            extend="both",
        )
    ),
    "pressure": ScalarMetricStrategy(
        ScalarRenderSpec(
            title="Pressure",
            unit_label="hPa",
            cmap="viridis",
            transform=pascal_to_hpa,
        )
    ),
    "precipitation": ScalarMetricStrategy(
        ScalarRenderSpec(
            title="Precipitation",
            unit_label="mm",
            cmap="Blues",
            extend="max",
        )
    ),
    "wind": WindStrategy(),
    "humidity": ScalarMetricStrategy(
        ScalarRenderSpec(
            title="Specific Humidity",
            unit_label="kg/kg",
            cmap="YlGnBu",
        )
    ),
}

def get_render_strategy(metric: str) -> RenderStrategy:
    strategy = _RENDERER.get(metric)
    if strategy is None:
        supported = ", ".join(sorted(_RENDERER))
        raise UnsupportedRenderMetricError(f"Unsupported render metric: {metric!r}. Supported metrics: {supported}")
    
    return strategy