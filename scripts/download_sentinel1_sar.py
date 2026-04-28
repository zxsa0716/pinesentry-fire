"""Sentinel-1 GRD SAR backscatter via Element84 STAC — cloud-free vegetation/SM proxy.

VV + VH polarizations over Uiseong/Sancheong pre-fire windows.
Public AWS Open Data, no auth.
"""
from __future__ import annotations

from pathlib import Path

from pystac_client import Client

STAC_URL = "https://earth-search.aws.element84.com/v1"
OUT_DIR = Path("data/sentinel1")

SITES = {
    "uiseong":   {"bbox": [128.50, 36.30, 128.90, 36.60], "dates": "2024-12-01/2025-03-22"},
    "sancheong": {"bbox": [127.70, 35.20, 128.00, 35.50], "dates": "2024-12-01/2025-03-21"},
    "gangneung": {"bbox": [128.78, 37.70, 128.95, 37.85], "dates": "2023-02-01/2023-04-11"},
    "uljin":     {"bbox": [129.20, 36.95, 129.60, 37.30], "dates": "2022-01-01/2022-03-04"},
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    c = Client.open(STAC_URL)
    summary = {}
    for site, info in SITES.items():
        items = list(c.search(
            collections=["sentinel-1-grd"],
            bbox=info["bbox"],
            datetime=info["dates"],
        ).item_collection())
        print(f"[{site}] {info['dates']}: {len(items)} S1 GRD scenes")
        summary[site] = len(items)
        for it in items[:3]:
            print(f"  - {it.id}  {it.datetime}")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()
