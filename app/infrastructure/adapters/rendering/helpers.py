import numpy as np

def to_2d_coords(lats: np.ndarray, lons: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if lats.ndim == 1 and lons.ndim == 1:
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        return lat_grid, lon_grid
    
    return lats, lons
