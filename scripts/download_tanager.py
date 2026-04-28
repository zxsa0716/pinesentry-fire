"""Download Tanager Open Data Catalog scenes for global sup-training.

Requires Planet account (https://www.planet.com/account/).
Set PL_API_KEY in environment before running.
"""
from __future__ import annotations

import os
from pathlib import Path

from pystac_client import Client

# Public Open Data STAC — Planet API key may be required for asset download
TANAGER_STAC = "https://www.planet.com/data/stac/browser/tanager-core-imagery/catalog.json"

# Global training scenes (5 forest sites)
SITES = {
    "bartlett":  [-71.30, 44.05, -71.27, 44.08],
    "niwot":     [-105.59, 40.03, -105.54, 40.06],
    "park_fire": [-121.7, 39.7, -121.3, 40.1],
    "palisades": [-118.58, 34.03, -118.49, 34.10],
    "tapajos":   [-55.10, -3.05, -54.90, -2.85],
}

# Korean wishlist verification (expected: 0 scenes)
KOREA_BBOX = [124.5, 33.0, 132.0, 39.0]

OUT_DIR = Path("data/tanager")


def walk_catalog(verbose: bool = True):
    """Walk the Tanager Open Data Catalog and report what's available."""
    c = Client.open(TANAGER_STAC)
    if verbose:
        print(f"Catalog: {c.title or 'tanager-core-imagery'}")
    for child in c.get_children():
        items = list(child.get_items())
        if verbose:
            print(f"  [{child.id}] {len(items)} scenes")
            for it in items[:3]:
                print(f"    - {it.id} ({it.datetime}) bbox={it.bbox}")
    return c


def search_site(c: Client, site: str, bbox: list, max_items: int = 5):
    items = c.search(bbox=bbox, max_items=max_items).item_collection()
    return items


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    c = walk_catalog()

    print("\n=== Global training site search ===")
    for site, bbox in SITES.items():
        items = search_site(c, site, bbox)
        print(f"  [{site}] {len(items)} candidate scenes")

    print("\n=== Korea verification (expected 0) ===")
    items = search_site(c, "korea", KOREA_BBOX, max_items=20)
    print(f"  Korean scenes: {len(items)} → {'CONFIRMED 0' if len(items) == 0 else 'UNEXPECTED'}")
    print("  → 30-scene wishlist 정당화 자료 (한반도 hyperspectral data desert)")


if __name__ == "__main__":
    if not os.getenv("PL_API_KEY"):
        print("[warn] PL_API_KEY not set — only catalog walk possible (no asset download)")
    main()
