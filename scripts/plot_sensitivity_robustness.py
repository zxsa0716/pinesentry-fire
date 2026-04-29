"""Visualize HSI v1 weight-sensitivity (A6 ablation) — supports OSF claim
that weights are physiologically motivated and NOT data-fit.

Reads {site}_sensitivity.json + spatial_cv.json and produces a 1×3 figure:
  Panel 1: weight perturbation AUC distribution (violin per site)
  Panel 2: spatial-block CV AUC distribution (per-fold strip per site)
  Panel 3: summary table — AUC ± std, 5-95% range
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("data/hsi/v1/sensitivity_robustness.png")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sites = ("uiseong", "sancheong")
    sens = {}
    cv = {}
    for s in sites:
        sp = Path(f"data/hsi/v1/{s}_sensitivity.json")
        cvp = Path(f"data/hsi/v1/{s}_spatial_cv.json")
        if sp.exists():
            sens[s] = json.loads(sp.read_text())
        if cvp.exists():
            cv[s] = json.loads(cvp.read_text())

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), gridspec_kw={"width_ratios": [1.5, 1.5, 1]})

    # Panel 1: weight perturbation
    ax = axes[0]
    centers = [sens[s]["auc_mean"] for s in sites if s in sens]
    q05 = [sens[s]["auc_q05"] for s in sites if s in sens]
    q95 = [sens[s]["auc_q95"] for s in sites if s in sens]
    site_names = [s.title() for s in sites if s in sens]
    x = np.arange(len(site_names))
    ax.errorbar(x, centers, yerr=[[c - lo for c, lo in zip(centers, q05)],
                                  [hi - c for c, hi in zip(centers, q95)]],
                fmt="o", color="#a50026", markersize=12, capsize=8, capthick=2, label="±20% weight perturbation (n=64)")
    ax.scatter(x, [0.747, 0.647][:len(x)], marker="*", s=180, color="#1a9850", zorder=5, label="Default OSF-pre-registered weights")
    ax.set_xticks(x); ax.set_xticklabels(site_names)
    ax.set_ylabel("ROC AUC")
    ax.set_title("A6 — Weight perturbation sensitivity (±20%)")
    ax.set_ylim(0.55, 0.80)
    ax.axhline(0.65, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: spatial-block CV
    ax = axes[1]
    for i, s in enumerate(sites):
        if s not in cv:
            continue
        folds = [f["auc"] for f in cv[s].get("folds", []) if f.get("auc") is not None]
        if folds:
            ax.scatter([i] * len(folds), folds, color=["#a50026", "#313695"][i],
                       s=120, alpha=0.6, label=f"{s.title()} (n={len(folds)} folds)")
            ax.hlines(np.mean(folds), i - 0.2, i + 0.2, color="black", linewidth=2)
    ax.set_xticks(np.arange(len(sites))); ax.set_xticklabels([s.title() for s in sites])
    ax.set_ylabel("ROC AUC")
    ax.set_title("A6 — Spatial-block CV (4×4 grid)")
    ax.set_ylim(0.40, 0.85)
    ax.axhline(0.65, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 3: summary table
    ax = axes[2]
    ax.axis("off")
    rows = [["Site", "Default", "±20% mean", "±20% range", "CV mean ± std"]]
    for s in sites:
        d = sens.get(s, {})
        c = cv.get(s, {})
        rows.append([
            s.title(),
            f"{0.747 if s == 'uiseong' else 0.647:.3f}",
            f"{d.get('auc_mean', float('nan')):.3f}",
            f"[{d.get('auc_q05', 0):.3f}, {d.get('auc_q95', 0):.3f}]",
            f"{c.get('auc_mean', float('nan')):.3f} ± {c.get('auc_std', 0):.3f}"
        ])
    tbl = ax.table(cellText=rows[1:], colLabels=rows[0], loc="center",
                   cellLoc="center", colWidths=[0.16, 0.16, 0.18, 0.25, 0.20])
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.8)
    ax.set_title("Summary (AUC)")

    fig.suptitle(
        "PineSentry-Fire v1 — A6 robustness: weights are NOT data-fit\n"
        "Default OSF-pre-registered weights vs ±20% perturbation vs spatial-block CV",
        fontsize=12, y=1.00,
    )
    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
