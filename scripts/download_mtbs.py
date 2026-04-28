"""Download MTBS US burn severity perimeters for PineSentry-Fire US validation.

No authentication required. Public USGS data.

Targets (v4.1 US Hero validation):
    - LA Palisades 2025-01 (primary US Hero, Tanager 5-month pre-fire window)
    - Park Fire 2024-07 (backup, no pre-fire Tanager but bonus post-fire)
    - Bridge Fire 2024-09 (backup)
    - Davis Fire 2024-09 (backup)
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import requests

MTBS_PERIMETERS_URL = (
    "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS_Fire/data/"
    "composite_data/burned_area_extent_shapefile/mtbs_perimeter_data.zip"
)

OUT_DIR = Path("data/mtbs")


def download_perimeters() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {MTBS_PERIMETERS_URL} ...")
    r = requests.get(MTBS_PERIMETERS_URL, timeout=300)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(OUT_DIR)
    print(f"Extracted to {OUT_DIR}")
    return OUT_DIR


def filter_target_fires():
    import geopandas as gpd

    out = OUT_DIR
    shp = next(out.glob("*.shp"), None)
    if shp is None:
        raise FileNotFoundError(f"No .shp under {out} — did download succeed?")

    gdf = gpd.read_file(shp)
    print(f"MTBS perimeters loaded: {len(gdf)} fires")

    targets = gdf[
        ((gdf.get("Incid_Name", "").str.upper().str.contains("PALISADES")) & (gdf["Ig_Date"].str.startswith("2025"))) |
        ((gdf.get("Incid_Name", "").str.upper().str.contains("PARK")) & (gdf["Ig_Date"].str.startswith("2024"))) |
        ((gdf.get("Incid_Name", "").str.upper().str.contains("BRIDGE")) & (gdf["Ig_Date"].str.startswith("2024"))) |
        ((gdf.get("Incid_Name", "").str.upper().str.contains("DAVIS")) & (gdf["Ig_Date"].str.startswith("2024")))
    ]

    print(f"Filtered targets: {len(targets)}")
    print(targets[["Incid_Name", "Ig_Date", "BurnBndAc"]].to_string())

    targets.to_file(OUT_DIR / "pinesentry_us_targets.gpkg", driver="GPKG")
    print(f"Saved → {OUT_DIR / 'pinesentry_us_targets.gpkg'}")
    return targets


if __name__ == "__main__":
    download_perimeters()
    filter_target_fires()
