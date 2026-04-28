"""Download GEDI L4A AGB (Above-Ground Biomass) over Korean peninsula + US sites.

Requires NASA EarthData URS account (https://urs.earthdata.nasa.gov/users/new).
"""
from __future__ import annotations

from pathlib import Path

import earthaccess

KOREAN_BBOX = (126.0, 33.0, 130.0, 38.5)
US_BBOXES = {
    "bartlett":  (-71.40, 44.00, -71.20, 44.15),
    "niwot":     (-105.60, 40.00, -105.50, 40.10),
    "park_fire": (-121.80, 39.65, -121.20, 40.20),
    "palisades": (-118.60, 34.00, -118.45, 34.15),
}

OUT_DIR = Path("data/gedi_l4a")
SHORT_NAME = "GEDI_L4A_AGB_Density_V2_1_2056"


def search_and_download(name: str, bbox, temporal=("2019-04-18", "2024-12-31")):
    out = OUT_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    print(f"Searching GEDI L4A for {name} bbox={bbox} ...")
    results = earthaccess.search_data(
        short_name=SHORT_NAME,
        bounding_box=bbox,
        temporal=temporal,
    )
    print(f"  → {len(results)} granules")
    if results:
        files = earthaccess.download(results[:50], str(out))  # first 50 to limit volume
        print(f"  Downloaded {len(files)} files to {out}")
    return results


def main():
    earthaccess.login(persist=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    search_and_download("korea", KOREAN_BBOX)
    for site, bbox in US_BBOXES.items():
        search_and_download(site, bbox)


if __name__ == "__main__":
    main()
