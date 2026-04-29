"""Multi-year NDVI anomaly per ROI from MOD13Q1 16-day composites.

For each fire site, compute the 2025-Mar NDVI relative to the 2020-2024
mean for the same DOY window. Strong negative anomaly → drought-stressed
canopy → potential fire risk feature for v1.5.

Output: data/mod13q1_ndvi/{roi}_ndvi_anomaly.tif (positive = drier than baseline)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SRC = Path("data/mod13q1_ndvi")
OUT = SRC / "anomaly"
OUT.mkdir(parents=True, exist_ok=True)

ROIS = {
    "uiseong":   (128.50, 36.30, 128.90, 36.60),
    "sancheong": (127.70, 35.20, 128.00, 35.50),
}


def main():
    files = sorted(SRC.glob("*.hdf"))
    print(f"MOD13Q1 files: {len(files)}")
    if not files:
        return

    try:
        from pyhdf.SD import SD, SDC
    except ImportError:
        print("pyhdf not installed (Python 3.14 wheel missing).", file=sys.stderr)
        print("Skipping NDVI anomaly extraction. Use 16-day NDVI directly via earthaccess in v2.")
        return

    # Per-tile aggregation per DOY: compute 2020-2024 mean DOY-by-DOY,
    # then 2025 anomaly = 2025 - mean, written to anomaly tif.
    print("Implementation deferred — needs pyhdf for HDF4 read.")


if __name__ == "__main__":
    main()
