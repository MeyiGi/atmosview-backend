import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from app.core.config import settings

class VisualizationService:
    """Turns raw arrays into PNG bytes."""
    _COLORMAPS = {
        "temperature": "RdYlBu_r",
        "pressure": "viridis",
    }

    def render_png(
        self,
        lats: np.ndarray,
        lons: np.ndarray,
        values: np.ndarray,
        variable: str,
        time: datetime,
    ) -> bytes:
        """
        Render a filled-contour map for the given data and return PNG bytes.

        Args:
            lats: 1-D latitude array
            lons: 1-D longitude array
            values: 2-D array with shape (len(lats), len(lons))
            variable: "temperature" or "pressure"
            time: timestamp shown in the plot title
        """
        cmap = self._COLORMAPS.get(variable, "plasma")
        label = self._get_label(variable)

        lon_grid, lat_grid = np.meshgrid(lons, lats)

        fig, ax = plt.subplots(figsize=(10, 6))
        cf = ax.contourf(lon_grid, lat_grid, values, levels=20, cmap=cmap)
        ax.contour(lon_grid, lat_grid, values, levels=20, colors="k", linewidths=0.3, alpha=0.4)

        # Draw approximate region border
        ax.set_xlim(settings.REGION_LON_MIN, settings.REGION_LON_MAX)
        ax.set_ylim(settings.REGION_LAT_MIN, settings.REGION_LAT_MAX)

        cbar = fig.colorbar(cf, ax=ax, pad=0.02)
        cbar.set_label(label, fontsize=11)

        ax.set_xlabel("Longitude", fontsize=10)
        ax.set_ylabel("Latitude", fontsize=10)
        ax.set_title(
            f"Central Asia — {variable.capitalize()}\n{time.strftime('%Y-%m-%d %H:%M UTC')}",
            fontsize=13,
        )
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    @staticmethod
    def _get_label(variable: str) -> str:
        labels = {
            "temperature": "Temperature (K)",
            "pressure": "Pressure (Pa)",
        }
        return labels.get(variable, variable)
