"""Download minimal EMIT pre-fire baseline scenes — v4.1 Dual Hero.

Per memory (CMR API verified 2026-04-25), the 2 critical baseline granules are:
    Uiseong:  EMIT_L2A_RFL_001_20240216T044207_2404703_007  (T-13mo, cc=21%)
    Sancheong: EMIT_L2A_RFL_001_20241219T032003_2435402_004  (T-3mo)

This script searches the full pre-fire window again (so you get the same
granules even if the memory IDs are stale), then keeps the WINTER scene
closest to the fire date — matching the target physiology.

Outputs to data/emit/{site}/. Skips if file already exists.

Usage:
    python scripts/download_emit.py            # download both baselines
    python scripts/download_emit.py --all      # download all candidates
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import earthaccess
except ImportError:
    print("Install: pip install earthaccess", file=sys.stderr)
    sys.exit(1)


SITES = {
    "uiseong": {
        "bbox": (128.50, 36.30, 128.90, 36.60),
        "fire_date": "2025-03-22",
    },
    "sancheong": {
        "bbox": (127.70, 35.20, 128.00, 35.50),
        "fire_date": "2025-03-21",
    },
}

EMIT_FIRST_LIGHT = "2022-08-01"


def parse_emit_datetime(granule_ur: str) -> datetime:
    """EMIT_L2A_RFL_001_<YYYYMMDD>T<HHMMSS>_..."""
    parts = granule_ur.split("_")
    for p in parts:
        if "T" in p and len(p) >= 15:
            try:
                return datetime.strptime(p[:15], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
    raise ValueError(f"cannot parse datetime from {granule_ur}")


def closest_pre_fire(results, fire_date: str, prefer_winter: bool = True):
    """Pick the granule closest to (but before) the fire date.

    If prefer_winter=True, restrict to Dec-Mar months (matches Korean spring
    fire season prep).
    """
    fire_dt = datetime.strptime(fire_date, "%Y-%m-%d")
    parsed = []
    for r in results:
        gid = r.get("umm", {}).get("GranuleUR", "")
        try:
            dt = parse_emit_datetime(gid)
        except Exception:
            continue
        if dt >= fire_dt:
            continue
        parsed.append((dt, r, gid))

    parsed.sort(key=lambda x: x[0], reverse=True)  # most recent first

    if prefer_winter:
        winter = [t for t in parsed if t[0].month in (12, 1, 2, 3)]
        if winter:
            return winter[0]

    if parsed:
        return parsed[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="download all candidates (~60 GB)")
    args = ap.parse_args()

    earthaccess.login(strategy="netrc")

    out_root = Path("data/emit")
    out_root.mkdir(parents=True, exist_ok=True)

    for site, info in SITES.items():
        site_dir = out_root / site
        site_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== [{site}] ===")
        print(f"window {EMIT_FIRST_LIGHT} ~ {info['fire_date']}, bbox={info['bbox']}")

        results = earthaccess.search_data(
            short_name="EMITL2ARFL",
            bounding_box=info["bbox"],
            temporal=(EMIT_FIRST_LIGHT, info["fire_date"]),
        )
        print(f"  candidates: {len(results)}")

        if args.all:
            to_dl = results
        else:
            picked = closest_pre_fire(results, info["fire_date"])
            if picked is None:
                print(f"  no pre-fire scene available — SKIP")
                continue
            dt, r, gid = picked
            print(f"  picked {gid}  ({dt.isoformat()})")
            to_dl = [r]

        files = earthaccess.download(to_dl, str(site_dir))
        print(f"  downloaded {len(files)} files → {site_dir}")


if __name__ == "__main__":
    main()
