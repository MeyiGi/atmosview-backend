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
from app.domain.exceptions import VariableNotFoundError
from app.infrastructure.config.settings import get_settings
from app.application.variable_specs.registry import get_variable_spec


class MatplotlibRenderer(WeatherRenderer):
    """Renders WeatherGrid objects into PNG bytes using matplotlib."""

    def render_wind_png(self, u_grid: WeatherGrid, v_grid: WeatherGrid) -> bytes:
        u = u_grid.values
        v = v_grid.values
        lats = u_grid.lats
        lons = u_grid.lons

        if lats.ndim == 1:
            lons_2d, lats_2d = np.meshgrid(lons, lats)
        else:
            lats_2d, lons_2d = lats, lons

        speed = np.sqrt(u ** 2 + v ** 2)

        fig, ax = plt.subplots(figsize=(10, 6))

        # Speed as background
        levels = np.linspace(speed.min(), speed.max(), 100)
        cf = ax.contourf(lons_2d, lats_2d, speed, levels=levels, cmap="YlOrRd", extend="both")
        cbar = fig.colorbar(cf, ax=ax, pad=0.02)
        cbar.set_label("Wind Speed (m/s)", fontsize=11)

        # Direction arrows — subsample so arrows don't overlap
        step = max(1, lats_2d.shape[0] // 20)
        ax.quiver(
            lons_2d[::step, ::step],
            lats_2d[::step, ::step],
            u[::step, ::step],
            v[::step, ::step],
            color="white",
            scale=150,
            width=0.003,
            alpha=0.8,
        )

        mean_lat = np.mean(lats_2d)
        ax.set_aspect(1.0 / np.cos(np.radians(mean_lat)))
        ax.set_xlim(np.min(lons_2d), np.max(lons_2d))
        ax.set_ylim(np.min(lats_2d), np.max(lats_2d))
        ax.set_xlabel("Longitude", fontsize=10)
        ax.set_ylabel("Latitude", fontsize=10)
        ax.set_title(
            f"Central Asia — Wind Speed & Direction\n"
            f"{u_grid.time.strftime('%Y-%m-%d %H:%M UTC')}",
            fontsize=13,
        )
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    
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