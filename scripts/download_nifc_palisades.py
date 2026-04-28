"""NIFC Wildland Fire Perimeter for Palisades 2025 (CA) — fills the MTBS gap.

NIFC publishes near-real-time Wildland Fire Perimeters via ArcGIS
FeatureServer:
  https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/
    WFIGS_Interagency_Perimeters/FeatureServer/0/query

Palisades Fire (LA, Jan 2025): Incident name 'Palisades' or
'Palisades Fire'; ignition 2025-01-07; ~23,000 acres burned.
"""
from __future__ import annotations

from pathlib import Path

import requests

OUT_DIR = Path("data/fire_perimeter")
SERVICE = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Interagency_Perimeters/FeatureServer/0/query"
)


def query_palisades():
    params = {
        "where": "poly_IncidentName LIKE '%PALISADES%' AND attr_FireDiscoveryDateTime >= timestamp '2025-01-01'",
        "outFields": "*",
        "f": "geojson",
        "outSR": 4326,
    }
    r = requests.get(SERVICE, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying NIFC WFIGS for Palisades 2025 ...")
    gj = query_palisades()
    n = len(gj.get("features", []))
    print(f"  features: {n}")
    out = OUT_DIR / "nifc_palisades_2025.geojson"
    out.write_text(__import__("json").dumps(gj, indent=2))
    print(f"  -> {out} ({out.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
