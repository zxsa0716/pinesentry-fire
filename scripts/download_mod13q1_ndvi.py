"""MOD13Q1 NDVI/EVI 16-day 250m for multi-year baseline + anomaly extraction.

Korean fire seasons (Mar-Apr) — compute multi-year mean NDVI and the
2025-Mar anomaly to feed the v1 NDVI_anomaly feature alongside HSI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import earthaccess

OUT_DIR = Path("data/mod13q1_ndvi")
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)


def main():
    earthaccess.login(strategy="netrc")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n=== MOD13Q1 over Korea, 2020-2025 spring ===")
    try:
        results = earthaccess.search_data(
            short_name="MOD13Q1",
            bounding_box=KOREA_BBOX,
            temporal=("2020-01-01", "2025-04-30"),
            count=120,
        )
        print(f"  results: {len(results)}")
        for r in results[:3]:
            print(f"    {r.get('umm', {}).get('GranuleUR', '?')}")
        if results:
            files = earthaccess.download(results[:60], str(OUT_DIR))
            print(f"  downloaded {len(files)} HDF files")
    except Exception as e:
        print(f"  failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
