"""Verify EMIT pre-fire scenes over Korean fire sites — v4.1 critical-path #1.

Run on Day 2 of project. Requires NASA EarthData URS account at
https://urs.earthdata.nasa.gov/users/new

Expected output (verified 2026-04-25 via NASA CMR API):
    Uiseong:   21 total / 2 clear (cc<50%)  — Primary Hero
    Sancheong: 14 total / 5 clear           — Secondary Hero (Dual)
    Gangneung:  0                            — NO-GO
    Uljin:      0 (EMIT first-light 2022-07) — NO-GO
"""
from __future__ import annotations

import sys
from datetime import datetime

try:
    import earthaccess
except ImportError:
    print("Install: pip install earthaccess", file=sys.stderr)
    sys.exit(1)


KOREAN_FIRES = {
    "uiseong": {
        "bbox": (128.50, 36.30, 128.90, 36.60),
        "fire_date": "2025-03-22",
        "expected_clear": 2,
    },
    "sancheong": {
        "bbox": (127.70, 35.20, 128.00, 35.50),
        "fire_date": "2025-03-21",
        "expected_clear": 5,
    },
    "gangneung": {
        "bbox": (128.78, 37.70, 128.95, 37.85),
        "fire_date": "2023-04-11",
        "expected_clear": 0,
    },
    "uljin": {
        "bbox": (129.20, 36.95, 129.60, 37.30),
        "fire_date": "2022-03-04",
        "expected_clear": 0,
    },
}

EMIT_FIRST_LIGHT = "2022-08-01"


def search_pre_fire(name: str, info: dict, cloud_threshold: float = 0.50):
    pre_start = EMIT_FIRST_LIGHT
    pre_end = info["fire_date"]
    print(f"\n[{name}] window {pre_start} ~ {pre_end}, bbox={info['bbox']}")

    results = earthaccess.search_data(
        short_name="EMITL2ARFL",
        bounding_box=info["bbox"],
        temporal=(pre_start, pre_end),
    )
    total = len(results)

    clear = []
    for r in results:
        cc = r.get("umm", {}).get("DataGranule", {}).get("CloudCover")
        if cc is not None and cc / 100.0 < cloud_threshold:
            clear.append(r)

    print(f"  total: {total} / clear (cc < {cloud_threshold*100:.0f}%): {len(clear)}")
    print(f"  expected clear: {info['expected_clear']} — {'PASS' if len(clear) >= info['expected_clear'] else 'CHECK'}")

    for r in clear[:5]:
        gid = r.get("umm", {}).get("GranuleUR", "?")
        cc = r.get("umm", {}).get("DataGranule", {}).get("CloudCover", "?")
        print(f"    {gid}  (cc={cc}%)")

    return total, clear


def hero_decision(results: dict[str, tuple[int, list]]) -> str:
    uiseong = len(results.get("uiseong", (0, []))[1])
    sancheong = len(results.get("sancheong", (0, []))[1])

    if uiseong >= 1 and sancheong >= 1:
        return "DUAL_HERO"
    if uiseong >= 1:
        return "UISEONG_ONLY"
    if sancheong >= 1:
        return "SANCHEONG_ONLY"
    return "FALLBACK_US_ONLY"


def main():
    print("=" * 70)
    print("PineSentry-Fire v4.1 — EMIT pre-fire scene verification (Korea)")
    print("=" * 70)
    earthaccess.login(persist=True)

    results = {}
    for name, info in KOREAN_FIRES.items():
        results[name] = search_pre_fire(name, info)

    decision = hero_decision(results)
    print(f"\n{'=' * 70}")
    print(f"HERO DECISION: {decision}")
    print(f"{'=' * 70}")

    if decision == "DUAL_HERO":
        print("→ Proceed with v4.1 DUAL HERO (Uiseong + Sancheong).")
    elif decision == "UISEONG_ONLY":
        print("→ Proceed with v4 single Hero (Uiseong).")
    elif decision == "SANCHEONG_ONLY":
        print("→ Proceed with v4 single Hero (Sancheong).")
    else:
        print("→ FALLBACK to US-only validation (LA Palisades + Park Fire).")
        print("   Korean component becomes 'pending Tanager 30-scene wishlist release'.")


if __name__ == "__main__":
    main()
