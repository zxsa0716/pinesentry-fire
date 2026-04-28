"""Download ECOSIS open-access leaf reflectance spectra for PROSPECT-D training.

ECOSIS (https://ecosis.org) is an open spectral library with thousands of
leaf-level hyperspectral measurements + paired traits (LMA, EWT, Cab, Cw).
Critical for training PROSPECT-D inversion (replace empirical proxies in v1).

Datasets prioritized (Korean + temperate conifer + Quercus):
  - 'fresh-leaf-spectra-of-7-broadleaf-species'
  - 'leaf-spectra-of-bartlett-experimental-forest'
  - 'fresh-and-dry-leaf-reflectance-and-transmittance-spectra-with-associated-leaf-traits-and-pigments'
  - 'angers-database'

API endpoint:
  https://ecosis.org/api/package/{slug}.json   — metadata
  Each package has CSV files via /api/package/{slug}/files

For now we just attempt a few well-known public packages.
"""
from __future__ import annotations

from pathlib import Path

import requests

OUT_DIR = Path("data/ecosis")

PACKAGES = [
    "fresh-leaf-spectra-to-estimate-leaf-mass-per-area-and-equivalent-water-thickness",
    "angers-leaf-optical-properties-database--lopex93-",
    "lopex93",
    "fresh-and-dry-leaf-reflectance-and-transmittance-spectra-with-associated-leaf-traits-and-pigments",
    "global-leaf-trait-spectra-from-the-bartlett-experimental-forest-bef",
    "leaf-level-spectra-from-niwot-ridge-co",
]

API_BASE = "https://ecosis.org/api/package"


def fetch_package(slug: str) -> dict | None:
    url = f"{API_BASE}/{slug}.json"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            print(f"  [{r.status_code}] {slug}")
            return None
        return r.json()
    except Exception as e:
        print(f"  [fail] {slug}: {e}")
        return None


def download_csv_files(meta: dict, dest: Path):
    files = meta.get("files", []) or meta.get("ckan_files", [])
    for f in files:
        name = f.get("filename") or f.get("name")
        url = f.get("url") or f.get("download_url")
        if not name or not url:
            continue
        if not name.lower().endswith((".csv", ".txt")):
            continue
        out = dest / name
        if out.exists():
            continue
        try:
            r = requests.get(url, timeout=300)
            if r.status_code != 200:
                continue
            out.write_bytes(r.content)
            print(f"  [ok] {name} ({out.stat().st_size/1024:.1f} KB)")
        except Exception as e:
            print(f"  [fail] {name}: {e}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug in PACKAGES:
        print(f"\n=== {slug} ===")
        meta = fetch_package(slug)
        if not meta:
            continue
        dest = OUT_DIR / slug
        dest.mkdir(parents=True, exist_ok=True)
        # Save metadata
        import json
        (dest / "_meta.json").write_text(json.dumps(meta, indent=2)[:50_000])
        download_csv_files(meta, dest)


if __name__ == "__main__":
    main()
