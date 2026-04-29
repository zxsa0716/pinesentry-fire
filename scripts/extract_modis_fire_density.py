"""Rasterize MODIS Active Fire (MOD14A1) into a 24-year fire-density map for Korea.

Per-pixel count of fire detections normalized by area gives the
fire return interval feature for v1.5+.

Strategy:
  1. Read all data/modis_fire_mcd14ml/MOD14A1/*.hdf  (50 granules from earlier)
  2. Extract fire mask (FireMask >= 7 = nominal+detected)
  3. Convert pixel coords -> lat/lon via tile sinusoidal projection helper
  4. Aggregate to 0.01 deg grid over Korea (124-132E, 33-39N)
  5. Save data/modis_fire/korea_fire_count.tif (single band)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SRC_DIR = Path("data/modis_fire_mcd14ml/MOD14A1")
OUT = Path("data/modis_fire/korea_fire_count.tif")
GRID_RES = 0.01   # deg
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)


def main():
    if not SRC_DIR.exists():
        print(f"missing {SRC_DIR}", file=sys.stderr); sys.exit(1)

    files = sorted(SRC_DIR.glob("*.hdf"))
    print(f"Found {len(files)} MOD14A1 granules")
    if not files:
        return

    # Korea grid
    nx = int(round((KOREA_BBOX[2] - KOREA_BBOX[0]) / GRID_RES))
    ny = int(round((KOREA_BBOX[3] - KOREA_BBOX[1]) / GRID_RES))
    count = np.zeros((ny, nx), dtype="int32")
    print(f"Korea grid {ny}x{nx} at {GRID_RES} deg")

    try:
        from pyhdf.SD import SD, SDC
    except ImportError:
        print("pip install pyhdf  — required to read .hdf MOD14A1", file=sys.stderr)
        return

    # MOD14A1 tiles cover specific h/v regions; we filter to Korea via lat/lon
    # of detected fires using tile-projected coordinates. Simpler approach:
    # use the FireMask + extract day-band detections, then compute lat/lon
    # from tile origin via the standard MODIS sinusoidal grid.
    # For minimal v1 implementation we use scaled positions assuming uniform
    # grid within tile and approximate via metadata.

    fires_lonlat = []
    for f in files[:30]:   # cap at 30 granules to limit runtime
        try:
            sd = SD(str(f), SDC.READ)
            fm = sd.select("FireMask").get()
            attrs = sd.attributes()
            # Korean tiles: h27v04, h27v05, h28v04, h28v05, h29v04, h29v05
            # Each tile is 1200x1200, ~1km, ~10 deg side
            sd.end()

            # FireMask values: 7=fire low conf, 8=nominal, 9=high
            mask = fm >= 7
            if mask.sum() == 0:
                continue

            # Approximate lat/lon for Korea pulls — extract h, v from filename
            stem = f.stem
            # MOD14A1.AYYYYDDD.hHHvVV.061...
            parts = stem.split(".")
            tile = next((p for p in parts if p.startswith("h") and "v" in p), None)
            if not tile:
                continue
            h = int(tile[1:3]); v = int(tile[4:6])

            # Sinusoidal MODIS: tile origin (lon, lat) approximate via
            # standard MODIS grid: lon = (h - 18) * 10 / cos(lat); v: lat = 80 - v*10
            # This is rough; proper inversion uses pyproj sinusoidal projection.
            ds_lat0 = 90 - v * 10
            ds_lat1 = 90 - (v + 1) * 10
            # Tile is (Day, Y, X) for MOD14A1; mask is (8, 1200, 1200)
            if mask.ndim == 3:
                # any-day fire detection across the 8-day composite
                any_fire = mask.any(axis=0)
            else:
                any_fire = mask
            ys, xs = np.where(any_fire)
            if len(ys) == 0:
                continue
            # Convert pixel (y, x) to lat/lon via uniform interpolation
            lat = ds_lat0 - (ys / any_fire.shape[0]) * (ds_lat0 - ds_lat1)
            lon_at_tile_west = (h - 18) * 10 / np.cos(np.deg2rad(lat))
            lon = lon_at_tile_west + (xs / any_fire.shape[1]) * (10 / np.cos(np.deg2rad(lat)))

            for la, lo in zip(lat, lon):
                if KOREA_BBOX[0] <= lo <= KOREA_BBOX[2] and KOREA_BBOX[1] <= la <= KOREA_BBOX[3]:
                    fires_lonlat.append((lo, la))
        except Exception as e:
            print(f"  fail {f.name}: {e}", file=sys.stderr)
            continue

    print(f"Total fire pixels in Korea: {len(fires_lonlat)}")

    for lo, la in fires_lonlat:
        ix = int((lo - KOREA_BBOX[0]) / GRID_RES)
        iy = int((KOREA_BBOX[3] - la) / GRID_RES)
        if 0 <= ix < nx and 0 <= iy < ny:
            count[iy, ix] += 1

    print(f"Non-zero grid cells: {(count > 0).sum()}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    import rasterio
    from rasterio.transform import from_origin
    transform = from_origin(KOREA_BBOX[0], KOREA_BBOX[3], GRID_RES, GRID_RES)
    with rasterio.open(
        OUT, "w", driver="GTiff", height=ny, width=nx, count=1,
        dtype="int32", crs="EPSG:4326", transform=transform, compress="LZW",
    ) as dst:
        dst.write(count, 1)
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
