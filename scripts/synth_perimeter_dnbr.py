"""Auto-synthesize fire perimeters from Sentinel-2 dNBR.

Backup for the data.go.kr 산불 피해지 polygon when the official
shapefile is not yet released for 2025 fires (Uiseong, Sancheong).

Method:
    NBR  = (NIR - SWIR2) / (NIR + SWIR2)
    dNBR = NBR_pre - NBR_post
    Burned: dNBR > 0.27 (Key & Benson 2006 USGS threshold)

Outputs:
    data/fire_perimeter/synth_{site}_dnbr.tif       — raster
    data/fire_perimeter/synth_{site}_dnbr.gpkg      — vectorized polygon

Pre-fire window: 30 days before fire date, cloud<20%
Post-fire window: 30 days after fire date, cloud<20%
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import rioxarray as rxr
import xarray as xr
from pystac_client import Client
from shapely.geometry import shape

STAC_URL = "https://earth-search.aws.element84.com/v1"
OUT_DIR = Path("data/fire_perimeter")

KOREAN_FIRES = {
    "uiseong":   {"bbox": [128.50, 36.30, 128.90, 36.60], "fire_date": "2025-03-22"},
    "sancheong": {"bbox": [127.70, 35.20, 128.00, 35.50], "fire_date": "2025-03-21"},
    "gangneung": {"bbox": [128.78, 37.70, 128.95, 37.85], "fire_date": "2023-04-11"},
    "uljin":     {"bbox": [129.20, 36.95, 129.60, 37.30], "fire_date": "2022-03-04"},
}

DNBR_THRESHOLD = 0.27


def _pick_least_cloudy(items, before: bool, fire_dt: date):
    """From STAC items, choose the item closest to (but on the correct side of) fire_dt
    with the lowest cloud cover. Returns None if no candidate."""
    if len(items) == 0:
        return None
    candidates = []
    for it in items:
        cc = it.properties.get("eo:cloud_cover", 100)
        dt = it.datetime.date()
        if before and dt >= fire_dt:
            continue
        if not before and dt <= fire_dt:
            continue
        candidates.append((cc, abs((dt - fire_dt).days), it))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def _read_band(item, asset_key: str, bbox):
    href = item.assets[asset_key].href
    arr = rxr.open_rasterio(href, masked=True).squeeze()
    arr = arr.rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    return arr.astype("float32")


def synth_one(site: str, info: dict):
    fire_dt = date.fromisoformat(info["fire_date"])
    bbox = info["bbox"]
    pre_start = (fire_dt - timedelta(days=60)).isoformat()
    pre_end = (fire_dt - timedelta(days=1)).isoformat()
    post_start = (fire_dt + timedelta(days=1)).isoformat()
    post_end = (fire_dt + timedelta(days=120)).isoformat()

    print(f"\n=== [{site}] fire {info['fire_date']} ===")
    print(f"  pre  window {pre_start} ~ {pre_end}")
    print(f"  post window {post_start} ~ {post_end}")

    c = Client.open(STAC_URL)
    pre_items = list(c.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{pre_start}/{pre_end}",
        query={"eo:cloud_cover": {"lt": 30}},
    ).item_collection())
    post_items = list(c.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{post_start}/{post_end}",
        query={"eo:cloud_cover": {"lt": 30}},
    ).item_collection())

    pre = _pick_least_cloudy(pre_items, before=True, fire_dt=fire_dt)
    post = _pick_least_cloudy(post_items, before=False, fire_dt=fire_dt)

    if pre is None or post is None:
        print(f"  SKIP: pre={pre is not None}, post={post is not None}")
        return

    print(f"  pre  scene: {pre.id}  cc={pre.properties.get('eo:cloud_cover')}%")
    print(f"  post scene: {post.id}  cc={post.properties.get('eo:cloud_cover')}%")

    # Element84 STAC asset names: nir = "nir" (B08, 10m), swir22 = "swir22" (B12, 20m)
    nir_pre = _read_band(pre, "nir", bbox)
    swir_pre = _read_band(pre, "swir22", bbox)
    nir_post = _read_band(post, "nir", bbox)
    swir_post = _read_band(post, "swir22", bbox)

    # Resample SWIR (20m) onto NIR (10m) grid for matched arithmetic
    swir_pre = swir_pre.rio.reproject_match(nir_pre)
    swir_post = swir_post.rio.reproject_match(nir_post)
    nir_post = nir_post.rio.reproject_match(nir_pre)
    swir_post = swir_post.rio.reproject_match(nir_pre)

    nbr_pre = (nir_pre - swir_pre) / (nir_pre + swir_pre + 1e-6)
    nbr_post = (nir_post - swir_post) / (nir_post + swir_post + 1e-6)
    dnbr = (nbr_pre - nbr_post).rename("dnbr")
    dnbr.attrs.update({
        "long_name": "Sentinel-2 dNBR (Key & Benson 2006)",
        "threshold_burned": DNBR_THRESHOLD,
        "pre_scene": pre.id,
        "post_scene": post.id,
    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raster_path = OUT_DIR / f"synth_{site}_dnbr.tif"
    dnbr.rio.to_raster(raster_path, compress="LZW", tiled=True)
    print(f"  raster -> {raster_path} ({raster_path.stat().st_size/1e6:.1f} MB)")

    # Vectorize burned mask
    burned = (dnbr > DNBR_THRESHOLD).astype("uint8")
    burned.rio.write_nodata(0, inplace=True)
    try:
        from rasterio.features import shapes as rio_shapes
        import geopandas as gpd

        with rxr.open_rasterio(raster_path) as src:
            arr = src.squeeze().values > DNBR_THRESHOLD
            tfm = src.rio.transform()
            crs = src.rio.crs
        polys = []
        for geom, val in rio_shapes(arr.astype("uint8"), mask=arr, transform=tfm):
            polys.append(shape(geom))
        if polys:
            n = len(polys)
            gdf = gpd.GeoDataFrame(
                {
                    "site": [site] * n,
                    "fire_date": [info["fire_date"]] * n,
                    "dnbr_threshold": [DNBR_THRESHOLD] * n,
                },
                geometry=polys, crs=crs,
            )
            gdf_out = gdf.dissolve(by="site").reset_index()
            vec_path = OUT_DIR / f"synth_{site}_dnbr.gpkg"
            gdf_out.to_file(vec_path, driver="GPKG")
            ha = gdf.to_crs("EPSG:5179").area.sum() / 10000
            print(f"  vector -> {vec_path}  ({len(gdf)} polygons, {ha:.0f} ha total)")
        else:
            print(f"  vector: no burned pixels above threshold")
    except Exception as e:
        print(f"  vectorize failed: {e}", file=sys.stderr)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for site, info in KOREAN_FIRES.items():
        try:
            synth_one(site, info)
        except Exception as e:
            print(f"  FAIL [{site}]: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
