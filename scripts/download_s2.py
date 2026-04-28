"""Download Sentinel-2 L2A baseline scenes for ablation A1 (Tanager vs S2).

Uses Element84 STAC on AWS Open Data — no authentication required.
"""
from __future__ import annotations

from pathlib import Path

from pystac_client import Client

STAC_URL = "https://earth-search.aws.element84.com/v1"
OUT_DIR = Path("data/s2_l2a")

# Same ROIs as Tanager / EMIT — match for ablation A1
SITES = {
    # Korean fires (validation)
    "uiseong":   {"bbox": [128.50, 36.30, 128.90, 36.60], "dates": ["2024-09-01/2025-04-01"]},
    "sancheong": {"bbox": [127.70, 35.20, 128.00, 35.50], "dates": ["2024-09-01/2025-04-01"]},
    "gangneung": {"bbox": [128.78, 37.70, 128.95, 37.85], "dates": ["2022-08-01/2023-05-01"]},
    "uljin":     {"bbox": [129.20, 36.95, 129.60, 37.30], "dates": ["2021-09-01/2022-04-01"]},
    "gwangneung":{"bbox": [127.10, 37.70, 127.20, 37.80], "dates": ["2024-08-01/2026-04-30"]},
    # US training/validation
    "bartlett":  {"bbox": [-71.30, 44.05, -71.27, 44.08], "dates": ["2023-06-01/2023-09-30"]},
    "niwot":     {"bbox": [-105.59, 40.03, -105.54, 40.06], "dates": ["2023-06-01/2023-09-30"]},
    "park_fire": {"bbox": [-121.7, 39.7, -121.3, 40.1], "dates": ["2024-04-01/2024-07-23"]},
    "palisades": {"bbox": [-118.58, 34.03, -118.49, 34.10], "dates": ["2024-08-01/2025-01-06"]},
    "tapajos":   {"bbox": [-55.10, -3.05, -54.90, -2.85], "dates": ["2024-06-01/2024-09-30"]},
}


def search_one(site: str, bbox, datetime_range: str, cloud_max: int = 20):
    c = Client.open(STAC_URL)
    items = c.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=datetime_range,
        query={"eo:cloud_cover": {"lt": cloud_max}},
    ).item_collection()
    return items


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for site, info in SITES.items():
        for dr in info["dates"]:
            items = search_one(site, info["bbox"], dr)
            print(f"[{site}] {dr}: {len(items)} S2 scenes (cloud<20%)")
            for it in items[:3]:
                print(f"  - {it.id} ({it.datetime})")
            summary[(site, dr)] = len(items)
    print("\nSummary:", summary)


if __name__ == "__main__":
    main()
