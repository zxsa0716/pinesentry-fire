"""Quick scan of TRY DB delivery — species + trait coverage."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

KOREAN_TARGETS = {
    "Pinus densiflora",
    "Pinus koraiensis",
    "Quercus mongolica",
    "Quercus serrata",
    "Quercus variabilis",
    "Quercus acutissima",
}


def main(path: str = "data/try/TRY_49341.tsv"):
    p = Path(path)
    if not p.exists():
        print(f"Not found: {p}", file=sys.stderr)
        sys.exit(1)

    species: set[str] = set()
    traits: dict[str, str] = {}
    rows_per_target: dict[str, int] = {sp: 0 for sp in KOREAN_TARGETS}
    rows_per_trait_for_targets: dict[str, dict[str, int]] = {}
    total_rows = 0

    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            total_rows += 1
            sp = (row.get("AccSpeciesName") or "").strip()
            tid = (row.get("TraitID") or "").strip()
            tnm = (row.get("TraitName") or "").strip()
            if sp:
                species.add(sp)
            if tid:
                traits.setdefault(tid, tnm)
            if sp in KOREAN_TARGETS:
                rows_per_target[sp] += 1
                rows_per_trait_for_targets.setdefault(sp, {}).setdefault(tid, 0)
                rows_per_trait_for_targets[sp][tid] += 1

    print(f"TRY 49341 delivery — total rows: {total_rows}")
    print(f"  unique species: {len(species)}")
    print(f"  unique traits:  {len(traits)}")

    print(f"\nKorean target species coverage:")
    found = 0
    for sp in sorted(KOREAN_TARGETS):
        n = rows_per_target.get(sp, 0)
        marker = "OK" if n > 0 else "MISS"
        print(f"  [{marker}] {sp}: {n} rows")
        if n > 0:
            found += 1
    print(f"  -> {found}/6 target species present")

    print(f"\nAll trait IDs returned ({len(traits)}):")
    for tid in sorted(traits.keys(), key=lambda x: int(x) if x.isdigit() else 99999):
        print(f"  {tid:>6}: {traits[tid][:90]}")

    if rows_per_trait_for_targets:
        print(f"\nKorean target rows per trait:")
        all_tids = sorted({t for d in rows_per_trait_for_targets.values() for t in d},
                          key=lambda x: int(x) if x.isdigit() else 99999)
        header = f"{'species':<25}" + "".join(f"{tid:>6}" for tid in all_tids)
        print(header)
        for sp in sorted(rows_per_trait_for_targets):
            row = f"{sp:<25}" + "".join(f"{rows_per_trait_for_targets[sp].get(t, 0):>6}" for t in all_tids)
            print(row)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/try/TRY_49341.tsv")
