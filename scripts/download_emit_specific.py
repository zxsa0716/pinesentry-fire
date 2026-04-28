"""Download a specific EMIT granule by ID — for memory-recommended baselines.

The auto-picker in download_emit.py chooses the date-closest scene, which
for Uiseong landed on 2025-01-31 — but that scene's tilted swath actually
misses the fire footprint.

Memory's pre-verified baselines (CMR API check 2026-04-25) are:
  Uiseong:  EMIT_L2A_RFL_001_20240216T044207_2404703_007 (T-13mo, cc=21%)

Run: python scripts/download_emit_specific.py
"""
from __future__ import annotations

from pathlib import Path

import earthaccess

GRANULES = {
    "uiseong": "EMIT_L2A_RFL_001_20240216T044207_2404703_007",
    # Memory mentioned a Sancheong T-3mo baseline but didn't verify the GranuleUR
    # — we already have a coverage-checked Sancheong scene from auto-pick, keep that.
}


def main():
    earthaccess.login(strategy="netrc")
    for site, gid in GRANULES.items():
        print(f"\n=== [{site}] specific granule: {gid} ===")
        results = earthaccess.search_data(short_name="EMITL2ARFL", granule_name=gid)
        print(f"  matches: {len(results)}")
        if not results:
            continue
        out = Path(f"data/emit/{site}")
        out.mkdir(parents=True, exist_ok=True)
        files = earthaccess.download(results, str(out))
        print(f"  files -> {files}")


if __name__ == "__main__":
    main()
