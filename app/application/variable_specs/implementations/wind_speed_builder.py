from app.application.variable_specs.builder import VariableSpecBuilder


class WindSpeedBuilder(VariableSpecBuilder):
    def build_name(self) -> None:
        self._name = "wind_speed"

    def build_colormap(self) -> None:
        self._colormap = "YlOrRd"

    def build_unit_label(self) -> None:
        self._unit_label = "Wind Speed (m/s)"