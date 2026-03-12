from app.domain.entities import VariableSpec
from app.application.variable_specs.implementations.temperature_builder import TemperatureBuilder
from app.application.variable_specs.implementations.pressure_builder import PressureBuilder
from app.domain.exceptions import VariableNotFoundError
from app.application.variable_specs.director import VariableSpecDirector


_BUILDERS = {
    "temperature" : TemperatureBuilder,
    "pressure" : PressureBuilder,
}


def get_variable_spec(name: str) -> VariableSpec:
    """"""
    builder_cls = _BUILDERS[name]
    
    if builder_cls is None:
        raise VariableNotFoundError(f"Unknown variable '{name}'. Available: {list(_BUILDERS)}")
    
    builder = builder_cls()
    director = VariableSpecDirector(builder)

    return director.construct()