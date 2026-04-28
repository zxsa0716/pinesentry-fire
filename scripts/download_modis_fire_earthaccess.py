"""MODIS Active Fire (MCD14ML) via NASA earthaccess — 24-year archive.

Replaces the FIRMS archive CSV approach (those URLs are 404 / require
free MAP_KEY). MCD14ML is the LANCE Earthdata standard MODIS active fire
monthly product, accessible with our existing URS account.
"""
from __future__ import annotations

import sys
from pathlib import Path

import earthaccess

OUT_DIR = Path("data/modis_fire_mcd14ml")
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)


def main():
    earthaccess.login(strategy="netrc")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Search MCD14DL — daily active fire (LANCE NRT) and archive
    for short_name in ("MOD14A1", "MYD14A1", "MOD14"):
        print(f"\n=== Searching {short_name} over Korea 2018-2025 ===")
        try:
            results = earthaccess.search_data(
                short_name=short_name,
                bounding_box=KOREA_BBOX,
                temporal=("2018-01-01", "2025-12-31"),
                count=200,
            )
            print(f"  results: {len(results)}")
            for r in results[:5]:
                gid = r.get("umm", {}).get("GranuleUR", "?")
                print(f"    {gid}")
            if results:
                # Download first ~50 to keep size manageable
                files = earthaccess.download(results[:50], str(OUT_DIR / short_name))
                print(f"  downloaded {len(files)} files")
                break  # success, no need to try other short_names
        except Exception as e:
            print(f"  search failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
