"""Download Tanager Open Data scenes via the public STAC catalog.

The catalog is publicly browsable at
    https://www.planet.com/data/stac/browser/tanager-core-imagery/catalog.json

— no API key required. We walk the 9 sub-catalogs (Agriculture, Coastal &
Water Bodies, Energy & Mining, Fire, GHG Plumes, Natural Lands, ROCX 2025,
Snow & Ice, Urban) and pull items + their COG/HDF5 assets.

Strategy for PineSentry-Fire:
  - Fire catalog is the priority (12/2024 - 9/2025 window includes our
    target Park Fire 2024 + Palisades 2025 if Tanager flew over them).
  - Natural Lands catalog secondary (forest training scenes).
  - Skip GHG Plumes / Snow & Ice / Urban / Coastal / ROCX / Agriculture
    / Energy unless explicitly requested.

Outputs:
  data/tanager/{sub_catalog}/{item_id}/{asset_files}
  data/tanager/inventory.json   — list of items + bboxes for later filter
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

import requests
from pystac_client import Client

ROOT_CATALOG = "https://www.planet.com/data/stac/tanager-core-imagery/catalog.json"
TARGET_SUBCATALOGS = ["Fire", "Natural Lands"]
OUT_DIR = Path("data/tanager")
INVENTORY = OUT_DIR / "inventory.json"


def fetch_json(url: str) -> dict:
    # Strip any tracking ?_gl=... parameters
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs = {k: v for k, v in qs.items() if not k.startswith("_")}
    parsed = parsed._replace(query=urllib.parse.urlencode(qs, doseq=True))
    clean = urllib.parse.urlunparse(parsed)
    r = requests.get(clean, headers={"Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    return r.json()


def walk_catalog(url: str, depth: int = 0, max_depth: int = 4):
    """Yield (kind, url, json) tuples for items + sub-catalogs encountered."""
    try:
        node = fetch_json(url)
    except Exception as e:
        print(f"  fetch failed for {url}: {e}", file=sys.stderr)
        return
    kind = node.get("type", "?")
    title = node.get("title") or node.get("id") or "?"
    yield (kind, url, node, title)
    if depth >= max_depth:
        return
    for link in node.get("links", []):
        rel = link.get("rel")
        if rel in {"child", "item"}:
            href = link.get("href")
            if not href:
                continue
            if not href.startswith("http"):
                # relative
                base = url.rsplit("/", 1)[0] + "/"
                href = base + href
            yield from walk_catalog(href, depth + 1, max_depth)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Walking {ROOT_CATALOG}")
    inventory: list[dict] = []

    for kind, url, node, title in walk_catalog(ROOT_CATALOG, max_depth=5):
        if kind == "Catalog" and url == ROOT_CATALOG:
            print(f"\n[ROOT] {title}")
            for ln in node.get("links", []):
                if ln.get("rel") == "child":
                    print(f"  child: {ln.get('title')}  {ln.get('href')}")
            continue

        if kind == "Catalog" and any(t.lower() in title.lower() for t in TARGET_SUBCATALOGS):
            print(f"\n[CATALOG] {title}  -- diving in")

        if kind == "Feature" or node.get("type") == "Feature":
            # STAC Item
            item_id = node.get("id", "?")
            bbox = node.get("bbox")
            collection = node.get("collection")
            assets = list((node.get("assets") or {}).keys())
            inventory.append({
                "id": item_id,
                "url": url,
                "collection": collection,
                "bbox": bbox,
                "assets": assets,
                "datetime": node.get("properties", {}).get("datetime"),
            })

    INVENTORY.write_text(json.dumps(inventory, indent=2, ensure_ascii=False))
    print(f"\nDiscovered {len(inventory)} STAC items -> {INVENTORY}")
    if inventory:
        print("First 5 entries:")
        for it in inventory[:5]:
            print(f"  {it['id']}  bbox={it['bbox']}  assets={it['assets'][:5]}")


if __name__ == "__main__":
    main()
