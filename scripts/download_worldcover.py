"""Download ESA WorldCover 10m land-cover for all ROIs.

WorldCover 2021 is the highest-res global land-cover product (10m).
Hosted free on AWS:
  s3://esa-worldcover/v200/2021/map/ESA_WorldCover_10m_2021_v200_{TILE}_Map.tif

Tiles are 3°x3° (e.g., N36E126). Naming: N{lat}{E/W}{lon} where lat
is the southern edge and lon the western edge.

Used as:
  - secondary land-cover label (cross-check imsangdo)
  - for sites outside Korea (Park Fire, Palisades) where no imsangdo
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import requests

OUT_DIR = Path("data/worldcover")
ROIS = {
    "uiseong":    (128.50, 36.30, 128.90, 36.60),
    "sancheong":  (127.70, 35.20, 128.00, 35.50),
    "gangneung":  (128.78, 37.70, 128.95, 37.85),
    "uljin":      (129.20, 36.95, 129.60, 37.30),
    "gwangneung": (127.10, 37.70, 127.20, 37.80),
    "jirisan":    (127.60, 35.20, 127.90, 35.50),
    "seorak":     (128.30, 38.00, 128.55, 38.20),
    "jeju":       (126.50, 33.20, 126.80, 33.40),
    "park_fire":  (-121.85, 39.65, -121.20, 40.15),
    "palisades":  (-118.60, 34.00, -118.45, 34.15),
    "bartlett":   (-71.40, 44.00, -71.20, 44.15),
    "niwot":      (-105.65, 40.00, -105.50, 40.10),
}

S3_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"


def tile_name(lon: int, lat: int) -> str:
    """Tile origin = southern + western corner, in 3° steps."""
    tlat = int(3 * np.floor(lat / 3.0))
    tlon = int(3 * np.floor(lon / 3.0))
    ns = "N" if tlat >= 0 else "S"
    ew = "E" if tlon >= 0 else "W"
    return f"{ns}{abs(tlat):02d}{ew}{abs(tlon):03d}"


def tiles_for_bbox(bbox) -> list[str]:
    lon_min, lat_min, lon_max, lat_max = bbox
    out = set()
    lons = range(int(3 * np.floor(lon_min / 3)), int(3 * np.floor(lon_max / 3)) + 1, 3)
    lats = range(int(3 * np.floor(lat_min / 3)), int(3 * np.floor(lat_max / 3)) + 1, 3)
    for lat in lats:
        for lon in lons:
            out.add(tile_name(lon, lat))
    return sorted(out)


def download_tile(name: str, dest: Path) -> bool:
    url = f"{S3_BASE}/ESA_WorldCover_10m_2021_v200_{name}_Map.tif"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return True
    try:
        with requests.get(url, stream=True, timeout=180) as r:
            if r.status_code == 404:
                print(f"  [404] {name}")
                return False
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"  [fail] {name}: {e}")
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tiles_dir = OUT_DIR / "tiles"
    tiles_dir.mkdir(exist_ok=True)

    import rioxarray as rxr
    from rasterio.merge import merge
    import rasterio

    for roi, bbox in ROIS.items():
        out_path = OUT_DIR / f"worldcover_{roi}.tif"
        if out_path.exists():
            print(f"[skip] {roi} -> {out_path.name}")
            continue
        tiles = tiles_for_bbox(bbox)
        print(f"\n=== {roi} bbox={bbox} tiles={tiles} ===")
        ok_paths = []
        for t in tiles:
            p = tiles_dir / f"{t}.tif"
            if download_tile(t, p):
                ok_paths.append(p)
                print(f"  [ok] {t}")

        if not ok_paths:
            continue
        srcs = [rasterio.open(p) for p in ok_paths]
        mosaic, transform = merge(srcs)
        profile = srcs[0].profile.copy()
        profile.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform, compress="LZW", tiled=True)
        for s in srcs:
            s.close()

        tmp = OUT_DIR / f"_tmp_{roi}.tif"
        with rasterio.open(tmp, "w", **profile) as dst:
            dst.write(mosaic)

        da = rxr.open_rasterio(tmp, masked=True)
        da_clip = da.rio.clip_box(*bbox)
        da_clip.rio.to_raster(out_path, compress="LZW", tiled=True)
        da.close()
        tmp.unlink(missing_ok=True)
        print(f"  -> {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
