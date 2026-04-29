"""Precision-Recall AUC + calibration curve for all 5 sites.

PR-AUC is more meaningful than ROC-AUC when the burned class is rare
(e.g., Sancheong has 252 burned / 9945 unburned ≈ 2.5%).

Calibration: bin HSI v1 score into deciles, plot empirical fire rate
per bin → ideally a 45° line means HSI v1 = 0.7 → 70% empirical risk.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")


def load_site(site):
    h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    if not h_path.exists():
        return None
    h = rxr.open_rasterio(h_path, masked=True).squeeze()
    peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
    if not peri_path.exists():
        return None
    return h, peri_path


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import precision_recall_curve, average_precision_score

    fig_pr, ax_pr = plt.subplots(figsize=(8, 6))
    fig_cal, ax_cal = plt.subplots(figsize=(8, 6))
    summary = {}

    colors = {"uiseong": "#a50026", "sancheong": "#313695",
              "gangneung": "#1a9850", "uljin": "#984ea3", "palisades": "#fdb863"}

    for site in SITES:
        loaded = load_site(site)
        if loaded is None:
            continue
        h, peri_path = loaded
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]
        unburned = h.values[(~burn) & valid]
        if len(burned) < 10:
            continue
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])

        # Precision-recall
        prec, rec, _ = precision_recall_curve(y, s)
        ap = average_precision_score(y, s)
        baseline_p = y.mean()
        ax_pr.plot(rec, prec, color=colors[site], linewidth=2,
                   label=f"{site.title()} AP={ap:.3f}  (positive base = {baseline_p:.3f})")

        # Calibration
        bins = np.linspace(0, 1, 11)
        bin_idx = np.digitize(s, bins) - 1
        bin_means = []
        bin_centers = []
        for b in range(10):
            m = bin_idx == b
            if m.sum() > 50:
                bin_means.append(y[m].mean())
                bin_centers.append((bins[b] + bins[b+1]) / 2)
        if bin_centers:
            ax_cal.plot(bin_centers, bin_means, "o-", color=colors[site],
                        linewidth=2, markersize=8, label=site.title())

        summary[site] = {
            "ap_pr_auc": float(ap),
            "positive_baseline": float(baseline_p),
            "pr_auc_lift_over_baseline": float(ap / max(baseline_p, 1e-9)),
            "n_burned": int(len(burned)),
            "n_unburned": int(len(unburned)),
        }
        print(f"  {site:>10}: PR-AUC = {ap:.3f}  (baseline {baseline_p:.3f}, lift {ap/baseline_p:.2f}x)")

    ax_pr.set_xlabel("Recall"); ax_pr.set_ylabel("Precision")
    ax_pr.set_title("PineSentry-Fire v1 — Precision-Recall (5 sites)")
    ax_pr.legend(loc="upper right", fontsize=9)
    ax_pr.set_xlim(0, 1); ax_pr.set_ylim(0, 1)
    ax_pr.grid(True, alpha=0.3)
    fig_pr.savefig("data/hsi/v1/pr_curves.png", dpi=140, bbox_inches="tight")
    plt.close(fig_pr)

    ax_cal.plot([0, 1], [0, 1], "--", color="grey", linewidth=1, label="Perfect calibration")
    ax_cal.set_xlabel("HSI v1 score (decile center)")
    ax_cal.set_ylabel("Empirical fire rate")
    ax_cal.set_title("PineSentry-Fire v1 — Calibration (5 sites)")
    ax_cal.legend(loc="upper left", fontsize=9)
    ax_cal.grid(True, alpha=0.3)
    fig_cal.savefig("data/hsi/v1/calibration.png", dpi=140, bbox_inches="tight")
    plt.close(fig_cal)

    Path("data/hsi/v1/pr_summary.json").write_text(json.dumps(summary, indent=2))
    print("\nsaved:")
    print("  data/hsi/v1/pr_curves.png")
    print("  data/hsi/v1/calibration.png")
    print("  data/hsi/v1/pr_summary.json")


if __name__ == "__main__":
    main()
