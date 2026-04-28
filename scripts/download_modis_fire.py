"""Download MODIS Active Fire 2000-2024 over Korea + 4 US sites.

MCD14ML (Combined Terra+Aqua active fire, monthly) — 1km, 24+ year history.
Free via NASA FIRMS (https://firms.modaps.eosdis.nasa.gov/).

Useful for:
  - 24-year fire return interval per pixel
  - frequency baseline (high-fire vs low-fire areas)
  - validate dNBR perimeter against historical Active Fire detections

API: https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{COUNTRY|XYXY}/{DAY_RANGE}

For deeper history (>2 years) use the FIRMS archive endpoint with map_key.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import requests

# Korea-wide bbox: 124-132E, 33-39N
# (FIRMS API expects west,south,east,north)
BBOX_KOREA = (124.0, 33.0, 132.0, 39.0)
BBOX_PARK = (-122.5, 39.5, -120.5, 40.5)
BBOX_PALISADES = (-119.0, 33.5, -118.0, 34.5)
BBOX_BARTLETT = (-72.0, 43.5, -70.5, 44.5)
BBOX_NIWOT = (-106.5, 39.5, -105.0, 40.5)

OUT_DIR = Path("data/modis_fire")

# FIRMS area API requires a MAP_KEY. We attempt the public archive endpoint
# which works for csv downloads of the last 10 days without a key, plus the
# Earthdata-cookie-based archive endpoint for older data.

ARCHIVE_BASE = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c61/csv"


def fetch_archive_year(year: int, region_name: str = "World", out: Path | None = None) -> Path | None:
    """Download a year of MODIS C6.1 active fire CSV (global)."""
    url = f"{ARCHIVE_BASE}/MODIS_C6_1_Global_{year}.csv"
    out = out or (OUT_DIR / f"MODIS_C6_1_Global_{year}.csv")
    if out.exists() and out.stat().st_size > 100_000:
        print(f"  [skip] {out.name}")
        return out
    try:
        with requests.get(url, stream=True, timeout=600) as r:
            if r.status_code != 200:
                print(f"  [{r.status_code}] {url}")
                return None
            with open(out, "wb") as f:
                for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                    f.write(chunk)
        print(f"  [ok] {url} -> {out.name} ({out.stat().st_size/1e6:.1f} MB)")
        return out
    except Exception as e:
        print(f"  [fail] {url}: {e}")
        return None


def filter_to_bbox(csv_path: Path, bbox, out_path: Path):
    """Filter the global CSV to a single bbox."""
    import pandas as pd
    chunks = []
    for chunk in pd.read_csv(csv_path, chunksize=200_000):
        m = (
            (chunk["longitude"] >= bbox[0]) & (chunk["longitude"] <= bbox[2]) &
            (chunk["latitude"] >= bbox[1]) & (chunk["latitude"] <= bbox[3])
        )
        sel = chunk[m]
        if len(sel):
            chunks.append(sel)
    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        df.to_csv(out_path, index=False)
        print(f"  filtered {len(df):,} rows -> {out_path.name}")
    else:
        print(f"  no rows in bbox for {csv_path.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Download recent years globally (since 2015 — 10 years of fire history)
    years = list(range(2015, 2025))
    yearly_csvs = []
    for y in years:
        p = fetch_archive_year(y)
        if p:
            yearly_csvs.append(p)

    # Filter to each region of interest
    regions = {
        "korea": BBOX_KOREA,
        "park_fire": BBOX_PARK,
        "palisades": BBOX_PALISADES,
        "bartlett": BBOX_BARTLETT,
        "niwot": BBOX_NIWOT,
    }
    for region, bbox in regions.items():
        out_dir = OUT_DIR / region
        out_dir.mkdir(exist_ok=True)
        print(f"\n=== Filter to {region} bbox={bbox} ===")
        for csv in yearly_csvs:
            year = csv.stem.split("_")[-1]
            out_path = out_dir / f"modis_{region}_{year}.csv"
            if out_path.exists():
                continue
            filter_to_bbox(csv, bbox, out_path)


if __name__ == "__main__":
    main()
