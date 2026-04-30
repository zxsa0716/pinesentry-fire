"""Wishlist HSI prioritization (v1.7 advancement, Tanager Q7 quantification).

Apply HSI v1 to each of the 30 Tanager wishlist points using the nearest
8-ROI atlas raster. Output a prioritized CSV: which 30 candidate Tanager
acquisitions are predicted to capture the highest-fire-risk pixels — i.e.
where Tanager 5 nm SWIR would be most informative.

Output: wishlist/korea_30_scenes_priority.csv + .json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

WISHLIST = Path("wishlist/korea_30_scenes.geojson")
ATLAS_DIR = Path("data/atlas")
OUT_CSV = Path("wishlist/korea_30_scenes_priority.csv")
OUT_JSON = Path("wishlist/korea_30_scenes_priority.json")

ROI_BBOXES = {  # rough WGS84 (lon_min, lat_min, lon_max, lat_max)
    "uiseong":   (128.40, 36.20, 129.00, 36.70),
    "sancheong": (127.60, 35.10, 128.10, 35.50),
    "gangneung": (128.70, 37.40, 129.10, 37.90),
    "uljin":     (129.20, 36.70, 129.50, 37.20),
    "gwangneung":(127.10, 37.70, 127.30, 37.90),
    "jirisan":   (127.50, 35.20, 127.90, 35.50),
    "seorak":    (128.30, 38.00, 128.60, 38.30),
    "jeju":      (126.20, 33.20, 126.80, 33.60),
}


def find_roi(lon, lat):
    for name, (x0, y0, x1, y1) in ROI_BBOXES.items():
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            return name
    # Fallback: closest by center
    best = None; best_d = 1e9
    for name, (x0, y0, x1, y1) in ROI_BBOXES.items():
        cx, cy = 0.5*(x0+x1), 0.5*(y0+y1)
        d = (lon - cx) ** 2 + (lat - cy) ** 2
        if d < best_d:
            best_d = d; best = name
    return best


def sample_hsi_at(lon, lat, da):
    da_wgs = da.rio.reproject("EPSG:4326")
    try:
        v = da_wgs.sel(x=lon, y=lat, method="nearest").item()
        return float(v) if np.isfinite(v) else None
    except Exception:
        return None


def main():
    if not WISHLIST.exists():
        print(f"missing {WISHLIST}", file=sys.stderr); return
    rows = json.loads(WISHLIST.read_text(encoding="utf-8"))["features"]

    # Load each ROI atlas raster once
    atlases = {}
    for roi in ROI_BBOXES:
        p = ATLAS_DIR / f"{roi}_hsi_v1.tif"
        if p.exists():
            atlases[roi] = rxr.open_rasterio(p, masked=True).squeeze()

    out = []
    for f in rows:
        props = f["properties"]
        geom = f["geometry"]
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
        elif geom["type"] == "Polygon":
            coords = np.array(geom["coordinates"][0])
            lon, lat = float(coords[:, 0].mean()), float(coords[:, 1].mean())
        else:
            continue
        roi = find_roi(lon, lat)
        hsi_value = sample_hsi_at(lon, lat, atlases[roi]) if roi in atlases else None
        out.append({
            "name": props.get("name", ""),
            "region": props.get("region", ""),
            "lon": lon, "lat": lat,
            "atlas_roi": roi,
            "predicted_HSI_v1": hsi_value,
            "user_priority": props.get("priority", ""),
            "note": props.get("note", ""),
        })

    # Sort by predicted HSI desc (None goes to bottom)
    out_sorted = sorted(out, key=lambda r: (r["predicted_HSI_v1"] is None,
                                            -(r["predicted_HSI_v1"] or 0)))

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_sorted[0].keys()))
        writer.writeheader(); writer.writerows(out_sorted)
    OUT_JSON.write_text(json.dumps(out_sorted, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"30 wishlist scenes ranked by predicted HSI v1:")
    for i, r in enumerate(out_sorted[:10], 1):
        h = r["predicted_HSI_v1"]
        h_str = f"{h:.3f}" if h is not None else "no-data"
        print(f"  {i:2d}. HSI={h_str}  {r['name'][:60]}  ({r['atlas_roi']})")
    print(f"\nsaved -> {OUT_CSV}")
    print(f"saved -> {OUT_JSON}")


if __name__ == "__main__":
    main()
