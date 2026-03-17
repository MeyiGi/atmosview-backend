import numpy as np
import matplotlib.pyplot as plt

from app.domain.entities import RenderRequest
from app.infrastructure.adapters.rendering.helpers import to_2d_coords
from app.infrastructure.adapters.rendering.specs import ScalarRenderSpec


class ScalarMetricStrategy:
    def __init__(self, spec: ScalarRenderSpec) -> None:
        self._spec = spec

    def render(self, request: RenderRequest):
        grid = request.grids["main"]
        lat_grid, lon_grid = to_2d_coords(grid.lats, grid.lons)
        values = self._spec.transform(np.copy(grid.values))

        fig, ax = plt.subplots(figsize=(10, 6))

        levels = self._spec.levels_builder(values)
        cf = ax.contourf(
            lon_grid,
            lat_grid,
            values,
            levels=levels,
            cmap=self._spec.cmap,
            extend=self._spec.extend,
        )

        ax.contour(
            lon_grid,
            lat_grid,
            values,
            levels=levels[::5],
            colors="k",
            linewidths=0.3,
            alpha=0.25,
        )

        mean_lat = float(np.mean(lat_grid))
        ax.set_aspect(1.0 / np.cos(np.radians(mean_lat)))
        ax.set_xlim(float(np.min(lon_grid)), float(np.max(lon_grid)))
        ax.set_ylim(float(np.min(lat_grid)), float(np.max(lat_grid)))

        cbar = fig.colorbar(cf, ax=ax, pad=0.02)
        cbar.set_label(self._spec.unit_label)

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(
            f"Central Asia — {self._spec.title}\n"
            f"{grid.time:%Y-%m-%d %H:%M UTC}"
        )
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
        fig.tight_layout()
        return fig