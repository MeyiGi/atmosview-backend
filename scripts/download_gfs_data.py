"""
scripts/download_gfs_data.py

Downloads GFS analysis fields and saves each variable
as a separate GRIB file directly under data/.

Usage:
    python3 scripts/download_gfs_data.py
    python3 scripts/download_gfs_data.py --date "2024-01-15 12:00"

Requires:
    pip install herbie-data
"""

import argparse
import shutil
from pathlib import Path
from dataclasses import dataclass

from herbie import Herbie


# ---------------------------------------------------------------------------
# Variable descriptors — add new variables here, nothing else changes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GfsVariable:
    search: str      # Herbie GRIB message search pattern (regex)
    filename: str    # target filename under data/


GFS_VARIABLES: list[GfsVariable] = [
    # GfsVariable(search=":TMP:2 m above ground:",      filename="temperature.grib"),
    # GfsVariable(search=":PRES:surface:",              filename="pressure.grib"),
    # GfsVariable(search=":APCP:surface:0-6 hour acc fcst:", filename="precipitation.grib"),
    # GfsVariable(search=":UGRD:10 m above ground:",         filename="wind_u.grib"),
    # GfsVariable(search=":VGRD:10 m above ground:",         filename="wind_v.grib"),
    # GfsVariable(search=":HGT:500 mb:",                filename="geopotential_500.grib"),
    GfsVariable(search=":RH:2 m above ground:",       filename="humidity.grib"),
]


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------
def _get_herbie(date: str, search: str) -> Herbie | None:
    """Find the first fxx that actually contains the requested variable."""
    for fxx in (6, 3, 12, 24):
        try:
            h = Herbie(date, model="gfs", product="pgrb2.0p25", fxx=fxx)
            inventory = h.inventory(search)
            if not inventory.empty:
                print(f"  Using fxx={fxx}")
                return h
        except Exception:
            continue
    return None

def download_all(date: str, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = data_dir / "_gfs_tmp"

    print(f"Downloading GFS data for {date}\n")

    for var in GFS_VARIABLES:
        dest = data_dir / var.filename
        print(f"  {var.search:<40} → {dest.name} ...", end=" ", flush=True)

        h = _get_herbie(date, var.search)
        if h is None:
            print("NOT FOUND in any fxx — skipped")
            continue

        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir()

        try:
            h.download(var.search, save_dir=tmp_dir)

            # Herbie sometimes saves files without extension — find any non-empty file
            downloaded = sorted(
                f for f in tmp_dir.rglob("*")
                if f.is_file() and f.stat().st_size > 0
            )

            if not downloaded:
                print("NOT FOUND after download — skipped")
                continue

            shutil.move(str(downloaded[0]), dest)
            print("OK")

        except Exception as exc:
            print(f"ERROR: {exc}")

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    print(f"\nDone. Files saved to {data_dir.resolve()}/")

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GFS data for Central Asia")
    parser.add_argument(
        "--date",
        default="2024-01-15 12:00",
        help="Analysis datetime, e.g. '2024-03-01 00:00'",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Target directory (default: data/)",
    )
    args = parser.parse_args()

    download_all(date=args.date, data_dir=Path(args.data_dir))