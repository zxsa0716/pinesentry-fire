"""Download Hyperion (EO-1) Gwangneung 2010-09-07 single bonus scene.

Reference: Park et al. 2019 ISPRS IJGI 8(3):150 — confirmed only 1 Hyperion
scene exists over the KNA (Gwangneung Arboretum) region.

Requires USGS EarthExplorer ERS account.
"""
from __future__ import annotations

import os
from pathlib import Path

OUT_DIR = Path("data/hyperion")

GWANGNEUNG_TARGET = {
    "dataset": "EO1_HYP_PUB",  # public Hyperion
    "bbox": (127.10, 37.70, 127.20, 37.80),
    "date": "2010-09-07",
}


def download_via_landsatxplore():
    try:
        from landsatxplore.api import API
    except ImportError:
        print("Install: pip install landsatxplore")
        raise

    user = os.getenv("USGS_USERNAME")
    pw = os.getenv("USGS_PASSWORD")
    if not (user and pw):
        print("Set USGS_USERNAME and USGS_PASSWORD env vars (https://ers.cr.usgs.gov)")
        return

    api = API(username=user, password=pw)
    scenes = api.search(
        dataset=GWANGNEUNG_TARGET["dataset"],
        bbox=GWANGNEUNG_TARGET["bbox"],
        start_date="2010-09-07",
        end_date="2010-09-08",
    )
    print(f"Found {len(scenes)} Hyperion scenes near Gwangneung 2010-09-07")
    if scenes:
        scene = scenes[0]
        print(f"  display_id: {scene['display_id']}")
        print(f"  entity_id:  {scene['entity_id']}")
        api.download(scene_id=scene["entity_id"], output_dir=str(OUT_DIR))
    api.logout()


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    download_via_landsatxplore()
