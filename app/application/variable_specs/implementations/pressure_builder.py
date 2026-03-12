from app.application.variable_specs.builder import VariableSpecBuilder


class PressureBuilder(VariableSpecBuilder):
    def build_name(self) -> None:
        self._name = "pressure"

    def build_colormap(self) -> None:
        self._colormap = "viridis"

    def build_unit_label(self) -> None:
        self._unit_label = "Pressure (Pa)"