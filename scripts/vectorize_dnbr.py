"""Vectorize already-computed dNBR rasters into burned polygons.

Standalone re-run of the vectorize step (the synth_perimeter_dnbr.py
raster step succeeded; only vectorization failed in the first pass).
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import rioxarray as rxr
from rasterio.features import shapes as rio_shapes
from shapely.geometry import shape

DNBR_THRESHOLD = 0.27
OUT_DIR = Path("data/fire_perimeter")

FIRE_DATES = {
    "uiseong":   "2025-03-22",
    "sancheong": "2025-03-21",
    "gangneung": "2023-04-11",
    "uljin":     "2022-03-04",
}


def vectorize(site: str, fire_date: str):
    raster = OUT_DIR / f"synth_{site}_dnbr.tif"
    if not raster.exists():
        print(f"[{site}] missing raster {raster}", file=sys.stderr)
        return
    with rxr.open_rasterio(raster) as src:
        arr = src.squeeze().values > DNBR_THRESHOLD
        tfm = src.rio.transform()
        crs = src.rio.crs

    polys = [shape(g) for g, v in rio_shapes(arr.astype("uint8"), mask=arr, transform=tfm)]
    if not polys:
        print(f"[{site}] no burned pixels above threshold")
        return

    n = len(polys)
    gdf = gpd.GeoDataFrame(
        {
            "site": [site] * n,
            "fire_date": [fire_date] * n,
            "dnbr_threshold": [DNBR_THRESHOLD] * n,
        },
        geometry=polys, crs=crs,
    )
    gdf_out = gdf.dissolve(by="site").reset_index()
    out = OUT_DIR / f"synth_{site}_dnbr.gpkg"
    gdf_out.to_file(out, driver="GPKG")

    ha = gdf.to_crs("EPSG:5179").area.sum() / 10000
    print(f"[{site}] {n} polygons -> {out}  ({ha:.0f} ha total)")


def main():
    for site, fd in FIRE_DATES.items():
        try:
            vectorize(site, fd)
        except Exception as e:
            print(f"[{site}] FAIL: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
