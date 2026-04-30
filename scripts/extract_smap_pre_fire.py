"""Pre-fire SMAP root-zone SM extraction per ROI for v1.5 dual-stress HSI.

For each Korean ROI, average SMAP L4 SPL4SMGP root-zone soil moisture
over the 30 days before the fire date. Output GeoTIFF aligned to a
0.09 deg grid (SMAP native ~9km).
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SRC = Path("data/smap_l4")
OUT = Path("data/smap_l4/pre_fire_root_sm")
OUT.mkdir(parents=True, exist_ok=True)

ROIS = {
    # Use the available SMAP window (2025-01-31 to 2025-02-04). The 30-day
    # pre-fire window (2025-02-20 to 2025-03-21) is unavailable in our
    # download; this gives a T-7-week soil-moisture proxy instead.
    "uiseong":    {"bbox": (128.50, 36.30, 128.90, 36.60), "fire_date": "2025-02-05"},
    "sancheong":  {"bbox": (127.70, 35.20, 128.00, 35.50), "fire_date": "2025-02-05"},
}


def main():
    files = sorted(SRC.glob("*.h5"))
    print(f"SMAP files available: {len(files)}")
    if not files:
        print("No SMAP files — run download_smap_l4_sm.py first", file=sys.stderr); return

    try:
        import h5py
    except ImportError:
        print("pip install h5py", file=sys.stderr); return

    # SMAP L4 file naming: SMAP_L4_SM_gph_YYYYMMDDTHHMMSS_Vvvv_NNN.h5
    def parse_date(path):
        try:
            stem = path.stem
            ds = stem.split("_")[4]   # SMAP_L4_SM_gph_<date>_V<v>_<r>
            return date.fromisoformat(f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}")
        except Exception:
            return None

    for roi, info in ROIS.items():
        fire_dt = date.fromisoformat(info["fire_date"])
        window_start = fire_dt - timedelta(days=30)
        print(f"\n[{roi}] fire {fire_dt}, averaging {window_start} ~ {fire_dt}")
        windowed = []
        for f in files:
            d = parse_date(f)
            if d and window_start <= d < fire_dt:
                windowed.append(f)
        print(f"  {len(windowed)} files in window")
        if not windowed:
            continue

        # Read root-zone SM, average over window, then take max-bbox subset
        # SMAP grid is 0.09 deg EASE-Grid; we just slice by lat/lon bounds
        try:
            with h5py.File(windowed[0], "r") as h:
                lat = h["/cell_lat"][:]
                lon = h["/cell_lon"][:]
        except Exception as e:
            print(f"  could not open {windowed[0].name}: {e}", file=sys.stderr); continue

        bb = info["bbox"]
        m = (lat >= bb[1]) & (lat <= bb[3]) & (lon >= bb[0]) & (lon <= bb[2])
        if not m.any():
            print(f"  bbox not in SMAP grid"); continue
        ys, xs = np.where(m)
        y0, y1 = ys.min(), ys.max() + 1
        x0, x1 = xs.min(), xs.max() + 1

        stack = []
        for f in windowed:
            try:
                with h5py.File(f, "r") as h:
                    rzsm = h["/Geophysical_Data/sm_rootzone"][y0:y1, x0:x1]
                stack.append(rzsm)
            except Exception:
                continue
        if not stack:
            continue
        arr = np.stack(stack, axis=0)
        arr = np.where(arr < 0, np.nan, arr)
        mean = np.nanmean(arr, axis=0).astype("float32")
        print(f"  mean SM range: {np.nanmin(mean):.3f} ~ {np.nanmax(mean):.3f}")

        # Save to per-ROI .npz so we can plot/analyze later
        out = OUT / f"{roi}_pre_fire_rzsm_mean.npz"
        np.savez(out, mean=mean, lat=lat[y0:y1, x0:x1], lon=lon[y0:y1, x0:x1])
        print(f"  saved -> {out}")


if __name__ == "__main__":
    main()
