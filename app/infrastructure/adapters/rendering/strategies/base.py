from typing import Protocol

from matplotlib.figure import Figure
from app.domain.entities import RenderRequest

class RenderStrategy(Protocol):
    def render(self, request: RenderRequest) -> Figure: ...