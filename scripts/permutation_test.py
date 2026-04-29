"""Permutation test for HSI v1 AUC null distribution.

Shuffle the burn label N times, compute AUC each time. The empirical
p-value = fraction of shuffles with AUC >= observed. If p < 0.001 we
reject the null hypothesis that HSI v1 has no relationship to burn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
N_PERM = 500


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(42)
    summary = {}
    fig, axes = plt.subplots(1, len(SITES), figsize=(20, 4))

    for ax, site in zip(axes.ravel(), SITES):
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        if not h_path.exists():
            ax.set_visible(False); continue
        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                    else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not peri_path.exists():
            ax.set_visible(False); continue
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]; unburned = h.values[(~burn) & valid]
        if len(burned) < 10:
            ax.set_visible(False); continue

        # Subsample large arrays
        n_b = min(len(burned), 5000)
        n_u = min(len(unburned), 50000)
        idx_b = rng.choice(len(burned), n_b, replace=False)
        idx_u = rng.choice(len(unburned), n_u, replace=False)
        sb = burned[idx_b]; su = unburned[idx_u]
        y = np.concatenate([np.ones(n_b), np.zeros(n_u)])
        s = np.concatenate([sb, su])
        observed_auc = roc_auc_score(y, s)

        # Permutation
        null_aucs = np.zeros(N_PERM, dtype="float32")
        for k in range(N_PERM):
            y_perm = rng.permutation(y)
            null_aucs[k] = roc_auc_score(y_perm, s)
        p_value = float((null_aucs >= observed_auc).mean())
        summary[site] = {
            "observed_auc": float(observed_auc),
            "n_perm": N_PERM,
            "null_mean": float(null_aucs.mean()),
            "null_std": float(null_aucs.std()),
            "p_value": p_value,
            "p_value_text": "< 1/N" if p_value == 0 else f"{p_value:.4f}",
        }
        print(f"  {site:>10}: AUC = {observed_auc:.3f}, null mean {null_aucs.mean():.3f}, p = {summary[site]['p_value_text']}")

        # Plot null distribution
        ax.hist(null_aucs, bins=30, color="grey", alpha=0.7)
        ax.axvline(observed_auc, color="red", linewidth=2, label=f"observed {observed_auc:.3f}")
        ax.set_xlabel("AUC under null"); ax.set_ylabel("count")
        ax.set_title(f"{site.title()}\np = {summary[site]['p_value_text']}", fontsize=10)
        ax.legend(fontsize=8)

    fig.suptitle(f"PineSentry-Fire v1 — permutation test (N={N_PERM})", fontsize=12, y=1.02)
    fig.tight_layout()
    out = Path("data/hsi/v1/permutation_null.png")
    fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close(fig)
    Path("data/hsi/v1/permutation_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
