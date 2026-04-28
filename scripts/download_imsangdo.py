"""Download 산림청 임상도 1:25,000 + 산불 GIS for Korean validation.

Requires data.go.kr 인증서 로그인 (set DATA_GO_KR_KEY in env).
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd

# WFS endpoint — open after data.go.kr cert login
IMSANGDO_WFS = "https://map.forest.go.kr/forest/geoserver/wfs"

OUT_DIR = Path("data/imsangdo")

ROIS = {
    "uiseong":    "128.50,36.30,128.90,36.60",
    "sancheong":  "127.70,35.20,128.00,35.50",
    "gangneung":  "128.78,37.70,128.95,37.85",
    "uljin":      "129.20,36.95,129.60,37.30",
    "gwangneung": "127.10,37.70,127.20,37.80",
    "jirisan":    "127.60,35.20,127.90,35.50",
    "seorak":     "128.30,38.00,128.55,38.20",
    "jeju":       "126.50,33.20,126.80,33.40",  # 한라산
}


def fetch_roi(roi: str, bbox: str):
    out = OUT_DIR / f"{roi}.gpkg"
    if out.exists():
        print(f"  [skip] {out} exists")
        return
    print(f"  fetching {roi} bbox={bbox} ...")
    url = (
        f"{IMSANGDO_WFS}?service=WFS&version=2.0.0&request=GetFeature"
        f"&typeName=imsangdo&bbox={bbox},EPSG:4326"
        f"&outputFormat=application/json"
    )
    try:
        gdf = gpd.read_file(url)
        gdf.to_file(out, driver="GPKG")
        print(f"    → {out} ({len(gdf)} polygons)")
    except Exception as e:
        print(f"    ERROR: {e}")
        print(f"    Try data.go.kr 인증서 login first or use alternative bulk download:")
        print(f"      https://www.data.go.kr/data/3045619/fileData.do")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for roi, bbox in ROIS.items():
        fetch_roi(roi, bbox)


if __name__ == "__main__":
    main()
