from abc import ABC, abstractmethod

from app.domain.entities import VariableSpec


class VariableSpecBuilder(ABC):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._name: str | None = None
        self._colormap: str | None = None
        self._unit_label: str | None = None

    @abstractmethod
    def build_name(self) -> None: ...

    @abstractmethod
    def build_colormap(self) -> None: ...

    @abstractmethod
    def build_unit_label(self) -> None: ...

    def get_result(self) -> VariableSpec:
        if None in (self._name, self._colormap, self._unit_label):
            raise ValueError("VariableSpec is not fully built")
        
        spec = VariableSpec(
            name=self._name,
            colormap=self._colormap,
            unit_label=self._unit_label,
        )
        self.reset()
        return spec