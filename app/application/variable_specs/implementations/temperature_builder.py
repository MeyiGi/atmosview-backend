from app.application.variable_specs.builder import VariableSpecBuilder


class TemperatureBuilder(VariableSpecBuilder):
    def build_name(self) -> None:
        self._name = "temperature"

    def build_colormap(self) -> None:
        self._colormap = "RdYlBu_r"

    def build_unit_label(self) -> None:
        self._unit_label = "Temperature (K)"