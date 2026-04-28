"""Clip 산림청 임상도 1:5,000 (TB_FGDI_FS_IM5000) FGDB to project ROIs.

Source: Esri File Geodatabase (4.14 GB nationwide).
Output: per-ROI GeoPackage with the fields needed for HSI species_map.

Run once after data.go.kr ZIP is extracted to:
    C:/Users/admin/Downloads/Tanager-Competition/데이터/임상도/TB_FGDI_FS_IM5000/
        TB_FGDI_FS_IM5000.gdb/

Outputs to data/imsangdo/{roi}.gpkg with columns:
    KOFTR_GROU_CD, FRTP_CD, DMCLS_CD, AGCLS_CD, DNST_CD, HEIGT_CD,
    KOFTR_NM, FRTP_NM, geometry
"""
from __future__ import annotations

import sys
from pathlib import Path

import pyogrio

GDB = Path(
    r"C:\Users\admin\Downloads\Tanager-Competition\데이터\임상도"
    r"\TB_FGDI_FS_IM5000\TB_FGDI_FS_IM5000.gdb"
)
LAYER = "TB_FGDI_FS_IM5000"
OUT_DIR = Path("data/imsangdo")

# (lon_min, lat_min, lon_max, lat_max) WGS84 — same as download_imsangdo.py
ROIS = {
    "uiseong":    (128.50, 36.30, 128.90, 36.60),
    "sancheong":  (127.70, 35.20, 128.00, 35.50),
    "gangneung":  (128.78, 37.70, 128.95, 37.85),
    "uljin":      (129.20, 36.95, 129.60, 37.30),
    "gwangneung": (127.10, 37.70, 127.20, 37.80),
    "jirisan":    (127.60, 35.20, 127.90, 35.50),
    "seorak":     (128.30, 38.00, 128.55, 38.20),
    "jeju":       (126.50, 33.20, 126.80, 33.40),
}

KEEP_COLS = [
    "STORUNST_CD", "FROR_CD", "FRTP_CD", "KOFTR_GROU_CD",
    "DMCLS_CD", "AGCLS_CD", "DNST_CD", "HEIGT_CD",
    "FRTP_NM", "KOFTR_NM", "DMCLS_NM", "AGCLS_NM", "DNST_NM",
    "MAP_LABEL_CD",
]


def main():
    if not GDB.exists():
        print(f"FGDB not found: {GDB}", file=sys.stderr)
        sys.exit(1)

    info = pyogrio.read_info(GDB, layer=LAYER)
    print(f"FGDB layer: {LAYER}")
    print(f"  features:  {info.get('features', '?')}")
    print(f"  CRS:       {info.get('crs', '?')}")
    print(f"  bounds:    {info.get('total_bounds', '?')}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    available = [f for f in info["fields"] if f in KEEP_COLS]
    print(f"  keep cols: {available}")

    import geopandas as gpd
    from shapely.geometry import box

    # Detect source CRS — Korean imsangdo is EPSG:5179 (Korea 2000 UTM-K)
    src_crs = info.get("crs")
    print(f"  source CRS = {src_crs}")

    for roi, bbox in ROIS.items():
        out = OUT_DIR / f"{roi}.gpkg"
        if out.exists():
            print(f"  [skip] {out} exists")
            continue

        # Build a WGS84 polygon for the ROI, project to source CRS
        roi_wgs = gpd.GeoSeries([box(*bbox)], crs="EPSG:4326")
        roi_src = roi_wgs.to_crs(src_crs)
        b_src = roi_src.total_bounds  # (xmin, ymin, xmax, ymax) in source CRS

        print(f"\n[{roi}] WGS84 bbox={bbox}")
        print(f"  reprojected to {src_crs}: {b_src}")

        gdf = pyogrio.read_dataframe(
            GDB, layer=LAYER,
            columns=available,
            bbox=tuple(b_src),
        )
        print(f"  features in bbox: {len(gdf)}")
        if len(gdf) == 0:
            print(f"  no features — skipping write")
            continue

        gdf.to_file(out, driver="GPKG")
        print(f"  -> {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
