import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.domain.entities import RenderRequest
from app.domain.interfaces import WeatherRenderer
from app.infrastructure.adapters.rendering.registry import get_render_strategy


class MatplotlibRenderer(WeatherRenderer):
    def render(self, request: RenderRequest) -> bytes:
        strategy = get_render_strategy(request.metric)
        fig = strategy.render(request)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()