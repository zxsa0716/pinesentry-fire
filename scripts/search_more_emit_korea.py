"""Expand EMIT coverage over Korean peninsula — beyond just Uiseong + Sancheong.

Strategy:
  - Search peninsula-wide (124-130E, 33-39N) for EMIT L2A scenes
  - Filter to scenes whose footprint contains at least one of our 8 ROIs
    (의성, 산청, 강릉, 울진, 광릉, 지리산, 설악, 제주)
  - Download up to 5 winter scenes per ROI

For v1 transferability across Korean peninsula.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import earthaccess

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


def parse_emit_dt(gid: str) -> datetime:
    for p in gid.split("_"):
        if "T" in p and len(p) >= 15:
            try:
                return datetime.strptime(p[:15], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
    raise ValueError(gid)


def covers_center(r, cx, cy) -> bool:
    try:
        polys = r.get("umm", {}).get("SpatialExtent", {}).get(
            "HorizontalSpatialDomain", {}).get("Geometry", {}).get("GPolygons", [])
        for poly in polys:
            pts = poly.get("Boundary", {}).get("Points", [])
            if not pts:
                continue
            xs = [p["Longitude"] for p in pts]
            ys = [p["Latitude"] for p in pts]
            if min(xs) <= cx <= max(xs) and min(ys) <= cy <= max(ys):
                return True
    except Exception:
        return False
    return False


def main():
    earthaccess.login(strategy="netrc")
    out_root = Path("data/emit")
    out_root.mkdir(parents=True, exist_ok=True)

    summary = {}
    for roi, bbox in ROIS.items():
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        print(f"\n=== [{roi}] center=({cx:.2f},{cy:.2f}) bbox={bbox} ===")
        results = earthaccess.search_data(
            short_name="EMITL2ARFL",
            bounding_box=bbox,
            temporal=("2022-08-01", "2026-04-28"),
        )
        covered = [r for r in results if covers_center(r, cx, cy)]
        print(f"  total={len(results)}  covers-center={len(covered)}")

        # Pick top 3 winter scenes (Dec/Jan/Feb/Mar)
        winter = []
        for r in covered:
            gid = r.get("umm", {}).get("GranuleUR", "")
            try:
                dt = parse_emit_dt(gid)
            except Exception:
                continue
            if dt.month in (12, 1, 2, 3):
                winter.append((dt, r, gid))
        winter.sort(key=lambda x: x[0], reverse=True)

        keep = winter[:3]
        site_dir = out_root / roi
        site_dir.mkdir(parents=True, exist_ok=True)
        existing = {p.name for p in site_dir.glob("*.nc")}
        to_dl = []
        for dt, r, gid in keep:
            if any(gid in n for n in existing):
                print(f"  [skip] {gid} (already have)")
                continue
            to_dl.append(r)
            print(f"  pick  {gid}  ({dt.isoformat()})")
        if to_dl:
            try:
                files = earthaccess.download(to_dl, str(site_dir))
                print(f"  downloaded {len(files)} files")
            except Exception as e:
                print(f"  download failed: {e}", file=sys.stderr)
        summary[roi] = {"total": len(results), "covered": len(covered), "kept": len(keep)}

    print("\n=== Summary ===")
    for roi, s in summary.items():
        print(f"  {roi:>10}: total={s['total']:>3}  covered={s['covered']:>3}  kept={s['kept']}")


if __name__ == "__main__":
    main()
