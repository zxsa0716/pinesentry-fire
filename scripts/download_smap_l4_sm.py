"""SMAP L4 SPL4SMGP 9km root-zone soil moisture for v1 dual-stress HSI.

Pre-fire (T-30 day) SMAP_L4 root-zone SM as a coarse proxy for soil
drought, complements canopy EWT from EMIT.
"""
from __future__ import annotations

import sys
from pathlib import Path

import earthaccess

OUT_DIR = Path("data/smap_l4")
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)


def main():
    earthaccess.login(strategy="netrc")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n=== SMAP L4 SPL4SMGP over Korea, Feb-Apr 2025 ===")
    try:
        results = earthaccess.search_data(
            short_name="SPL4SMGP",
            bounding_box=KOREA_BBOX,
            temporal=("2025-02-01", "2025-04-15"),
            count=80,
        )
        print(f"  results: {len(results)}")
        if results:
            files = earthaccess.download(results[:30], str(OUT_DIR))
            print(f"  downloaded {len(files)} files")
    except Exception as e:
        print(f"  failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
