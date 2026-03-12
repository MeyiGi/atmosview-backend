from app.domain.entities import VariableSpec
from app.application.variable_specs.builder import VariableSpecBuilder


class VariableSpecDirector:
    def __init__(self, builder: VariableSpecBuilder) -> None:
        self._builder = builder

    def construct(self) -> VariableSpec:
        self._builder.build_name()
        self._builder.build_colormap()
        self._builder.build_unit_label()
        return self._builder.get_result()