import numpy as np
import matplotlib.pyplot as plt

from app.domain.entities import RenderRequest
from app.infrastructure.adapters.rendering.helpers import to_2d_coords


class WindStrategy:
    def render(self, request: RenderRequest):
        u_grid = request.grids["u"]
        v_grid = request.grids["v"]

        u = u_grid.values
        v = v_grid.values
        lat_grid, lon_grid = to_2d_coords(u_grid.lats, u_grid.lons)

        speed = np.sqrt(u ** 2 + v ** 2)

        fig, ax = plt.subplots(figsize=(10, 6))

        levels = np.linspace(float(np.nanmin(speed)), float(np.nanmax(speed)), 100)
        cf = ax.contourf(
            lon_grid,
            lat_grid,
            speed,
            levels=levels,
            cmap="YlOrRd",
            extend="both",
        )

        step = max(1, lat_grid.shape[0] // 20)
        ax.quiver(
            lon_grid[::step, ::step],
            lat_grid[::step, ::step],
            u[::step, ::step],
            v[::step, ::step],
            color="white",
            scale=150,
            width=0.003,
            alpha=0.8,
        )

        mean_lat = float(np.mean(lat_grid))
        ax.set_aspect(1.0 / np.cos(np.radians(mean_lat)))
        ax.set_xlim(float(np.min(lon_grid)), float(np.max(lon_grid)))
        ax.set_ylim(float(np.min(lat_grid)), float(np.max(lat_grid)))

        cbar = fig.colorbar(cf, ax=ax, pad=0.02)
        cbar.set_label("Wind Speed (m/s)")

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(
            f"Central Asia — Wind Speed & Direction\n"
            f"{u_grid.time:%Y-%m-%d %H:%M UTC}"
        )
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
        fig.tight_layout()
        return fig