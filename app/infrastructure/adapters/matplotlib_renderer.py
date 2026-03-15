"""
infrastructure/adapters/matplotlib_renderer.py

Adapter that implements WeatherRenderer using matplotlib.

Swapping the renderer (e.g. to Plotly or Pillow) means writing a new
class that implements WeatherRenderer and wiring it in the DI container —
nothing else changes.
"""

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # must precede any other matplotlib import
import matplotlib.pyplot as plt
import numpy as np

from app.domain.entities import WeatherGrid
from app.domain.interfaces import WeatherRenderer
from app.domain.variable_registry import get_variable_spec
from app.domain.exceptions import VariableNotFoundError
from app.infrastructure.config.settings import get_settings


class MatplotlibRenderer(WeatherRenderer):
    """Renders WeatherGrid objects into PNG bytes using matplotlib."""

    def render_png(self, grid: WeatherGrid) -> bytes:
        try:
            spec = get_variable_spec(grid.variable)
            cmap = spec.colormap
            unit_label = spec.unit_label
        except VariableNotFoundError:
            cmap = "plasma"
            unit_label = grid.variable

        settings = get_settings()
        lats, lons = grid.lats, grid.lons
        
        # Копируем массив, чтобы не менять исходные данные объекта
        values = np.copy(grid.values)

        # Конвертация температуры из Кельвинов в Цельсии
        var_name = grid.variable.upper()
        if var_name in ("T2", "TEMP", "TC") or unit_label == "K":
            values = values - 273.15
            unit_label = "°C"
        elif var_name in ("RAINC", "RAINNC", "PRECIPITATION"):
            # WRF cumulative rain fields are already in mm — no conversion needed
            unit_label = "mm"

        # Build 2-D coordinate grids if inputs are 1-D (GRIB path)
        if lats.ndim == 1 and lons.ndim == 1:
            lon_grid, lat_grid = np.meshgrid(lons, lats)
        else:
            lat_grid = lats
            lon_grid = lons

        fig, ax = plt.subplots(figsize=(10, 6))

        if lats.ndim == 1:
            cf = ax.contourf(lon_grid, lat_grid, values, levels=20, cmap=cmap)
            ax.contour(
                lon_grid, lat_grid, values,
                levels=20, colors="k", linewidths=0.3, alpha=0.4,
            )
            ax.set_xlim(settings.REGION_LON_MIN, settings.REGION_LON_MAX)
            ax.set_ylim(settings.REGION_LAT_MIN, settings.REGION_LAT_MAX)
        else:
            vmin, vmax = np.min(values), np.max(values)
            
            # Approximate proper aspect ratio for mid-latitudes
            mean_lat = np.mean(lat_grid)
            ax.set_aspect(1.0 / np.cos(np.radians(mean_lat)))
            
            # Smooth continuous gradient
            levels = np.linspace(vmin, vmax, 100)
            cf = ax.contourf(
                lon_grid, lat_grid, values, 
                levels=levels, cmap=cmap, extend="both", antialiased=True
            )

            ax.set_xlim(np.min(lon_grid), np.max(lon_grid))
            ax.set_ylim(np.min(lat_grid), np.max(lat_grid))

        cbar = fig.colorbar(cf, ax=ax, pad=0.02)
        cbar.set_label(unit_label, fontsize=11)

        ax.set_xlabel("Longitude", fontsize=10)
        ax.set_ylabel("Latitude", fontsize=10)
        ax.set_title(
            f"Central Asia — {grid.variable.replace('_', ' ').capitalize()}\n"
            f"{grid.time.strftime('%Y-%m-%d %H:%M UTC')}",
            fontsize=13,
        )
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        
        return buf.read()