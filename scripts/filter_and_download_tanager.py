"""From the 270-item Tanager STAC inventory, pick scenes whose bbox
intersects our 4 target sites (Park Fire, Palisades, Bartlett, Niwot)
and download just the surface-reflectance HDF5 + UDM assets.

Skips radiance HDF5 to halve disk usage; we'll work from `basic_sr_hdf5`
or `ortho_*` if surface reflectance is not present.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

import requests

INV = Path("data/tanager/inventory.json")
OUT_ROOT = Path("data/tanager")

# (name, lon_min, lat_min, lon_max, lat_max)
TARGETS = {
    "park_fire":  (-121.85, 39.65, -121.20, 40.15),
    "palisades":  (-118.60, 34.00, -118.45, 34.15),
    "bartlett":   (-71.40, 44.00, -71.20, 44.15),
    "niwot":      (-105.65, 40.00, -105.50, 40.10),
    # Korean wishlist (almost certainly empty — log only)
    "uiseong_check":   (128.50, 36.30, 128.90, 36.60),
    "sancheong_check": (127.70, 35.20, 128.00, 35.50),
}

PREFER_ASSETS = ["basic_sr_hdf5", "ortho_beta_sr", "ortho_sr_hdf5"]


def bbox_overlap(a, b) -> bool:
    return not (a[0] > b[2] or a[2] < b[0] or a[1] > b[3] or a[3] < b[1])


def main():
    if not INV.exists():
        print("Run scripts/download_tanager_public.py first.", file=sys.stderr)
        sys.exit(1)
    inventory = json.loads(INV.read_text())
    print(f"Loaded {len(inventory)} STAC items")

    matches: dict[str, list[dict]] = {k: [] for k in TARGETS}
    for it in inventory:
        bb = it.get("bbox")
        if not bb or len(bb) != 4:
            continue
        for site, target_bb in TARGETS.items():
            if bbox_overlap(bb, target_bb):
                matches[site].append(it)

    for site, items in matches.items():
        print(f"\n[{site}] {len(items)} matching scene(s)")
        for it in items[:5]:
            print(f"  {it['id']}  {it.get('datetime', '?')}  bbox={it['bbox']}  assets={it['assets'][:6]}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")

    # Download SR HDF5 + UDM for the 4 NON-Korean target sites
    download_sites = {k: v for k, v in matches.items() if not k.endswith("_check")}
    for site, items in download_sites.items():
        if not items:
            continue
        site_dir = OUT_ROOT / site
        site_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== Downloading {site} ({len(items)} scenes) ===")
        for it in items:
            item_url = it["url"]
            item_dir = site_dir / it["id"]
            item_dir.mkdir(parents=True, exist_ok=True)
            try:
                r = requests.get(item_url, headers={"Accept": "application/json"}, timeout=60)
                r.raise_for_status()
                item_json = r.json()
            except Exception as e:
                print(f"  fetch item failed: {e}")
                continue

            assets = item_json.get("assets", {})
            picked = None
            for key in PREFER_ASSETS:
                if key in assets:
                    picked = (key, assets[key])
                    break
            if not picked:
                print(f"  {it['id']}: no SR asset (have {list(assets.keys())})")
                continue
            asset_key, asset = picked
            href = asset.get("href")
            if not href:
                continue
            fname = href.split("?")[0].rsplit("/", 1)[-1]
            out = item_dir / fname
            if out.exists() and out.stat().st_size > 100_000:
                print(f"  [skip] {fname} exists ({out.stat().st_size/1e9:.2f} GB)")
                continue
            print(f"  fetching {asset_key}: {href[:80]}...")
            try:
                with requests.get(href, stream=True, timeout=900) as r2:
                    r2.raise_for_status()
                    total = 0
                    with open(out, "wb") as f:
                        for chunk in r2.iter_content(chunk_size=4 * 1024 * 1024):
                            f.write(chunk)
                            total += len(chunk)
                print(f"    -> {out.name} ({total/1e9:.2f} GB)")
            except Exception as e:
                print(f"    download failed: {e}")
                if out.exists() and out.stat().st_size < 100_000:
                    out.unlink()


if __name__ == "__main__":
    main()
