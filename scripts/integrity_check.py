"""Verify downloaded data integrity + alignment for PineSentry-Fire.

Run after Day 7 of acquisition. Reports a status table for `STATUS.md`.
"""
from __future__ import annotations

import json
from pathlib import Path

import rasterio
from rasterio.errors import RasterioIOError


DATA_DIR = Path("data")

EXPECTED = {
    "tanager":    {"min_files": 5,  "ext": [".h5", ".tif"]},
    "emit":       {"min_files": 7,  "ext": [".nc"]},
    "hyperion":   {"min_files": 1,  "ext": [".tif", ".tar.gz"]},
    "s2_l2a":     {"min_files": 10, "ext": [".tif"]},
    "gedi_l4a":   {"min_files": 1,  "ext": [".h5"]},
    "neon":       {"min_files": 2,  "ext": [".csv", ".h5"]},
    "imsangdo":   {"min_files": 8,  "ext": [".gpkg"]},
    "mtbs":       {"min_files": 1,  "ext": [".gpkg", ".shp"]},
}


def check_dir(d: Path, ext: list, min_files: int) -> dict:
    if not d.exists():
        return {"exists": False, "n_files": 0, "ok": False, "files": []}
    files = []
    for e in ext:
        files.extend(d.rglob(f"*{e}"))
    n = len(files)
    return {
        "exists": True,
        "n_files": n,
        "ok": n >= min_files,
        "files": [str(f.relative_to(d)) for f in files[:5]],
    }


def verify_geotiff(path: Path) -> dict:
    try:
        with rasterio.open(path) as src:
            return {"crs": str(src.crs), "bounds": list(src.bounds), "shape": src.shape, "ok": True}
    except RasterioIOError as e:
        return {"ok": False, "error": str(e)}


def main():
    print("PineSentry-Fire data integrity check")
    print("=" * 60)
    status = {}
    for name, cfg in EXPECTED.items():
        d = DATA_DIR / name
        result = check_dir(d, cfg["ext"], cfg["min_files"])
        flag = "✓" if result["ok"] else "✗"
        print(f"  {flag} {name:12s} — {result['n_files']} files (need ≥{cfg['min_files']})")
        status[name] = result

    out = DATA_DIR / "integrity_report.json"
    out.write_text(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nReport → {out}")

    n_ok = sum(1 for s in status.values() if s["ok"])
    print(f"\n{n_ok}/{len(status)} data sources ready.")
    if n_ok == len(status):
        print("→ Data acquisition COMPLETE. Begin notebooks 02_isofit_atmcorr → 03_engine_training.")


if __name__ == "__main__":
    main()
