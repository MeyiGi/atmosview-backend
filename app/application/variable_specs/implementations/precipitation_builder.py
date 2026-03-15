from app.application.variable_specs.builder import VariableSpecBuilder


class PrecipitationBuilder(VariableSpecBuilder):
    def build_name(self) -> None:
        self._name = "precipitation"

    def build_colormap(self) -> None:
        self._colormap = "Blues"

    def build_unit_label(self) -> None:
        self._unit_label = "Precipitation (mm)"