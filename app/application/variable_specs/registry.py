from app.application.variable_specs.builder import VariableSpecBuilder
from app.application.variable_specs.implementations.humidity import HumidityBuilder
from app.application.variable_specs.implementations.wind_direction_builder import WindDirectionBuilder
from app.application.variable_specs.implementations.wind_speed_builder import WindSpeedBuilder
from app.application.variable_specs.implementations.temperature_builder import TemperatureBuilder
from app.application.variable_specs.implementations.pressure_builder import PressureBuilder
from app.application.variable_specs.implementations.precipitation_builder import PrecipitationBuilder
from app.application.variable_specs.director import VariableSpecDirector
from app.domain.exceptions import VariableNotFoundError
from app.domain.entities import VariableSpec


_BUILDERS: dict[str, type[VariableSpecBuilder]] = {
    "temperature" : TemperatureBuilder,
    "pressure" : PressureBuilder,
    "precipitation": PrecipitationBuilder,
    "wind_speed":    WindSpeedBuilder,
    "wind_direction": WindDirectionBuilder,
    "humidity":       HumidityBuilder,
}


def get_variable_spec(name: str) -> VariableSpec:
    builder_cls = _BUILDERS.get(name)
    
    if builder_cls is None:
        raise VariableNotFoundError(f"Unknown variable '{name}'. Available: {list(_BUILDERS)}")
    
    builder = builder_cls()
    director = VariableSpecDirector(builder)

    return director.construct()

def all_variable_names() -> list[str]:
    return list(_BUILDERS)