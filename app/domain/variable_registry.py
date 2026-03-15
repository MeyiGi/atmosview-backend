"""
domain/variable_registry.py

Central registry that maps variable names to their VariableSpec.
Adding a new weather variable is a one-liner here; no new endpoint
or branching logic needed anywhere else.
"""

from app.domain.entities import VariableSpec
from app.domain.exceptions import VariableNotFoundError

_REGISTRY: dict[str, VariableSpec] = {
    "temperature": VariableSpec(name="temperature", colormap="RdYlBu_r", unit_label="Temperature (K)"),
    "pressure":    VariableSpec(name="pressure",    colormap="viridis",   unit_label="Pressure (Pa)"),
    "precipitation": VariableSpec(name="precipitation", colormap="Blues", unit_label="Precipitation (mm)"),
    "wind_speed":    VariableSpec(name="wind_speed",    colormap="YlOrRd", unit_label="Wind Speed (m/s)"),
    "wind_direction": VariableSpec(name="wind_direction", colormap="hsv",  unit_label="Wind Direction (°)"),
}


def get_variable_spec(name: str) -> VariableSpec:
    """
    Return the VariableSpec for *name*.

    Raises:
        VariableNotFoundError: if the variable is not registered.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise VariableNotFoundError(
            f"Unknown variable '{name}'. "
            f"Available: {list(_REGISTRY)}"
        )


def all_variable_names() -> list[str]:
    return list(_REGISTRY)
