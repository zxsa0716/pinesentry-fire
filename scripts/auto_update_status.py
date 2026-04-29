"""Auto-generate STATUS.md from data/ contents and v1 evaluation files.

Scans every data/ subdir, computes file count + size, and writes a fresh
inventory table + per-site v1 AUC summary. Run after any new commit that
adds data layers.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DATA = Path("data")
OUT = Path("STATUS.md")


def dir_summary(p: Path) -> tuple[int, float]:
    files = [f for f in p.rglob("*") if f.is_file()]
    if not files:
        return 0, 0.0
    return len(files), sum(f.stat().st_size for f in files) / 1e9


def parse_v1_aucs() -> dict[str, dict]:
    """Read each {site}_eval_v1.png is hard; parse {site}_spatial_cv.json instead."""
    out = {}
    for site in ("uiseong", "sancheong", "gangneung", "uljin"):
        cv = Path(f"data/hsi/v1/{site}_spatial_cv.json")
        if cv.exists():
            try:
                d = json.loads(cv.read_text())
                out[site] = d
            except Exception:
                pass
    return out


def main():
    rows = []
    total_files = 0
    total_gb = 0.0
    for sub in sorted(DATA.iterdir()):
        if not sub.is_dir():
            continue
        n, gb = dir_summary(sub)
        if n == 0:
            continue
        total_files += n
        total_gb += gb
        rows.append((sub.name, n, gb))

    cv = parse_v1_aucs()

    lines = [
        f"# PineSentry-Fire — STATUS (auto-generated {date.today().isoformat()})",
        "",
        "## Data inventory (auto-scan)",
        "",
        "| Layer | Files | Size (GB) |",
        "|---|---:|---:|",
    ]
    for name, n, gb in rows:
        lines.append(f"| {name} | {n} | {gb:.2f} |")
    lines.append(f"| **Total** | **{total_files}** | **{total_gb:.2f}** |")
    lines.append("")

    if cv:
        lines += [
            "## v1 spatial-block CV (4×4 blocks)",
            "",
            "| Site | Folds w/ signal | AUC mean | AUC std | AUC range |",
            "|---|---:|---:|---:|---|",
        ]
        for site, d in cv.items():
            n_folds = d.get("n_folds_with_signal", "?")
            mean = d.get("auc_mean", float("nan"))
            std = d.get("auc_std", float("nan"))
            mn = d.get("auc_min", float("nan"))
            mx = d.get("auc_max", float("nan"))
            lines.append(f"| {site} | {n_folds} | {mean:.3f} | {std:.3f} | [{mn:.3f}, {mx:.3f}] |")
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} — {total_files} files / {total_gb:.2f} GB")


if __name__ == "__main__":
    main()
