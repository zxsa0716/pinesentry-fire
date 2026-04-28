"""Download NEON CFC + LMA tables — modern neonutilities API.

CFC: DP1.30012.001 — leaf chemistry table
LMA: DP1.10026.001 — leaf mass per area table

Returns a dict of pandas DataFrames; we serialize each to data/neon/{name}/.
Skips DP3.30006.002 AOP raster (too heavy without explicit need).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from neonutilities import load_by_product

OUT = Path("data/neon")
SITES = ["BART", "NIWO"]


def save_bundle(bundle, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    summary = {}
    for key, val in bundle.items():
        try:
            import pandas as pd
            if isinstance(val, pd.DataFrame):
                csv_path = dest / f"{key}.csv"
                val.to_csv(csv_path, index=False)
                summary[key] = {"type": "DataFrame", "rows": len(val), "cols": list(val.columns), "path": str(csv_path.name)}
                print(f"    {key}: {len(val)} rows -> {csv_path.name}")
            else:
                summary[key] = {"type": type(val).__name__, "repr": repr(val)[:200]}
                print(f"    {key}: {type(val).__name__} (not DataFrame, skipped)")
        except Exception as e:
            summary[key] = {"error": str(e)}
            print(f"    {key}: ERROR {e}")
    (dest / "_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for prod, name in [("DP1.30012.001", "cfc"), ("DP1.10026.001", "lma")]:
        save = OUT / name
        print(f"\n=== {prod} ({name}) sites={SITES} ===")
        try:
            bundle = load_by_product(
                dpid=prod,
                site=SITES,
                startdate="2023-01",
                enddate="2024-12",
                check_size=False,
                progress=False,
            )
        except Exception as e:
            print(f"  load failed: {e}", file=sys.stderr)
            continue

        if not isinstance(bundle, dict):
            print(f"  unexpected return type {type(bundle).__name__}")
            continue
        save_bundle(bundle, save)

    print(f"\nNEON tables -> {OUT.resolve()}")


if __name__ == "__main__":
    main()
