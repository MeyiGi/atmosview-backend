import glob
import os
from io import BytesIO

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response


router = APIRouter()

WRF_DIR = os.getenv("WRF_DIR", "/wrf")


def _latest_wrfout() -> str:
    files = sorted(glob.glob(os.path.join(WRF_DIR, "wrfout_d01_*")))
    if not files:
        raise HTTPException(status_code=404, detail=f"No wrfout files found in {WRF_DIR}")
    return files[-1]


def _wrfout_by_time(t: str) -> str:
    # t: YYYY-MM-DD_HH:MM:SS
    path = os.path.join(WRF_DIR, f"wrfout_d01_{t}")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"wrfout not found: {path}")
    return path


def _plot_png(arr2d: np.ndarray, title: str, label: str) -> bytes:
    plt.figure(figsize=(10, 6))
    plt.imshow(arr2d)
    plt.colorbar(label=label)
    plt.title(title)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf.read()


@router.get("/wrf/temperature")
def wrf_temperature(time: str | None = None):
    """
    time: YYYY-MM-DD_HH:MM:SS (пример: 2026-03-05_10:00:00)
    если time не задан — берём последний wrfout
    """
    path = _wrfout_by_time(time) if time else _latest_wrfout()
    ds = xr.open_dataset(path)

    if "T2" not in ds:
        raise HTTPException(status_code=500, detail="Variable T2 not found in wrfout")

    t2_k = ds["T2"].values  # (Time, y, x)
    t2_c = t2_k[0, :, :] - 273.15

    png = _plot_png(t2_c, f"WRF T2 (°C) | {os.path.basename(path)}", "°C")
    return Response(content=png, media_type="image/png")


@router.get("/wrf/pressure")
def wrf_pressure(time: str | None = None):
    """
    PSFC (Pa) -> hPa
    """
    path = _wrfout_by_time(time) if time else _latest_wrfout()
    ds = xr.open_dataset(path)

    if "PSFC" not in ds:
        raise HTTPException(status_code=500, detail="Variable PSFC not found in wrfout")

    psfc_pa = ds["PSFC"].values
    psfc_hpa = psfc_pa[0, :, :] / 100.0

    png = _plot_png(psfc_hpa, f"WRF PSFC (hPa) | {os.path.basename(path)}", "hPa")
    return Response(content=png, media_type="image/png")
@router.get("/wrf/meta")
def wrf_meta():
    import glob, os
    import xarray as xr
    from fastapi import HTTPException

    files = sorted(glob.glob(os.path.join(WRF_DIR, "wrfout_d01_*")))
    if not files:
        raise HTTPException(status_code=404, detail=f"No wrfout files found in {WRF_DIR}")

    latest = files[-1]
    ds = xr.open_dataset(latest)

    # XLAT/XLONG бывают (Time, y, x) или (y, x)
    if "XLAT" not in ds or "XLONG" not in ds:
        raise HTTPException(status_code=500, detail="XLAT/XLONG not found in wrfout")

    lats = ds["XLAT"].values
    lons = ds["XLONG"].values
    if lats.ndim == 3:
        lats = lats[0]
    if lons.ndim == 3:
        lons = lons[0]

    south = float(lats.min())
    north = float(lats.max())
    west  = float(lons.min())
    east  = float(lons.max())

    times = [os.path.basename(f).replace("wrfout_d01_", "") for f in files]
    return {"bounds": [[south, west], [north, east]], "times": times}