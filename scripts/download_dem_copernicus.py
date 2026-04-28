"""Download Copernicus 30m DEM (COP-DEM-GLO-30) for all ROIs.

DEM is ESSENTIAL for fire prediction:
  - slope: steeper -> faster fire spread
  - aspect: south-facing slopes drier in N hemisphere
  - elevation: temperature lapse rate

COP-DEM-GLO-30 is hosted free on AWS Open Data:
  s3://copernicus-dem-30m/{TILE}/{TILE}.tif
  no auth required.

Tile naming: Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM (1° tiles).

Outputs: data/dem/copdem30_{roi}.tif (clipped to ROI).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import requests

OUT_DIR = Path("data/dem")
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

S3_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"


def tile_name(lon: int, lat: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"


def tiles_for_bbox(bbox) -> list[str]:
    lon_min, lat_min, lon_max, lat_max = bbox
    lons = range(int(np.floor(lon_min)), int(np.floor(lon_max)) + 1)
    lats = range(int(np.floor(lat_min)), int(np.floor(lat_max)) + 1)
    return [tile_name(l, lat) for lat in lats for l in lons]


def download_tile(name: str, dest: Path) -> bool:
    url = f"{S3_BASE}/{name}/{name}.tif"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return True
    try:
        with requests.get(url, stream=True, timeout=180) as r:
            if r.status_code == 404:
                print(f"  [404] {name} (no land tile)")
                return False
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"  [fail] {name}: {e}")
        if dest.exists() and dest.stat().st_size < 1_000_000:
            dest.unlink()
        return False


def merge_and_clip(roi: str, bbox, tile_paths: list[Path]):
    """Merge tiles and clip to ROI bbox."""
    import rioxarray as rxr
    from rasterio.merge import merge
    import rasterio

    ok = [p for p in tile_paths if p.exists()]
    if not ok:
        return None
    print(f"  merging {len(ok)} tiles ...")
    srcs = [rasterio.open(p) for p in ok]
    mosaic, transform = merge(srcs)
    profile = srcs[0].profile.copy()
    profile.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform, compress="LZW", tiled=True)
    for s in srcs:
        s.close()

    # Write merged to a tmp file first, then clip via rioxarray
    tmp = OUT_DIR / f"_tmp_{roi}.tif"
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(mosaic)

    out = OUT_DIR / f"copdem30_{roi}.tif"
    da = rxr.open_rasterio(tmp, masked=True)
    da_clip = da.rio.clip_box(*bbox)
    da_clip.rio.to_raster(out, compress="LZW", tiled=True)
    da.close()
    tmp.unlink(missing_ok=True)
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tiles_dir = OUT_DIR / "tiles"
    tiles_dir.mkdir(exist_ok=True)

    for roi, bbox in ROIS.items():
        print(f"\n=== {roi} bbox={bbox} ===")
        tiles = tiles_for_bbox(bbox)
        print(f"  tiles needed: {tiles}")
        ok_paths = []
        for t in tiles:
            p = tiles_dir / f"{t}.tif"
            if download_tile(t, p):
                ok_paths.append(p)
                size_mb = p.stat().st_size / 1e6
                print(f"  [ok] {t} ({size_mb:.1f} MB)")

        if ok_paths:
            try:
                out = merge_and_clip(roi, bbox, ok_paths)
                if out:
                    print(f"  -> {out} ({out.stat().st_size/1e6:.1f} MB)")
            except Exception as e:
                print(f"  merge/clip failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
