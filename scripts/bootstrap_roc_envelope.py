"""Bootstrap 95% ROC envelope for all 5 sites (v1.7 advancement).

For each site, draw n_boot=200 bootstrap resamples with replacement,
compute the ROC curve on each resample, and shade the 2.5-97.5
percentile envelope around the central ROC. Reviewers immediately see
the AUC uncertainty as a SHAPE, not just a CI number.

Output: data/hsi/v1/HERO_roc_envelope.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT = Path("data/hsi/v1/HERO_roc_envelope.png")
SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
N_BOOT = 200
N_THRESH = 100


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve

    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.ravel()
    summary = {}

    for ax, site in zip(axes, SITES):
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                    else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not h_path.exists() or not peri_path.exists():
            ax.set_visible(False); continue
        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]
        unburned = h.values[(~burn) & valid]
        if len(burned) < 10: continue

        # Subsample for speed
        n_b = min(len(burned), 5000); n_u = min(len(unburned), 50000)
        bi = rng.choice(len(burned), n_b, replace=False)
        ui = rng.choice(len(unburned), n_u, replace=False)
        burned = burned[bi]; unburned = unburned[ui]
        y = np.concatenate([np.ones(n_b), np.zeros(n_u)])
        s = np.concatenate([burned, unburned])

        # Master ROC
        fpr0, tpr0, _ = roc_curve(y, s)
        auc0 = float(roc_auc_score(y, s))

        # Bootstrap on a common FPR grid
        fpr_grid = np.linspace(0, 1, N_THRESH)
        tpr_boot = np.zeros((N_BOOT, N_THRESH))
        aucs = np.zeros(N_BOOT)
        for k in range(N_BOOT):
            idx = rng.integers(0, len(y), len(y))
            yb = y[idx]; sb = s[idx]
            try:
                fpr_k, tpr_k, _ = roc_curve(yb, sb)
                tpr_boot[k] = np.interp(fpr_grid, fpr_k, tpr_k)
                aucs[k] = roc_auc_score(yb, sb)
            except Exception:
                tpr_boot[k] = np.nan; aucs[k] = np.nan
        valid_runs = np.isfinite(aucs)
        tpr_boot = tpr_boot[valid_runs]
        aucs = aucs[valid_runs]
        lower = np.percentile(tpr_boot, 2.5, axis=0)
        upper = np.percentile(tpr_boot, 97.5, axis=0)

        ax.fill_between(fpr_grid, lower, upper, color="#fdae61", alpha=0.40, label="95% bootstrap envelope")
        ax.plot(fpr0, tpr0, color="#a50026", linewidth=2,
                label=f"observed AUC = {auc0:.3f}\n95% CI [{aucs.min():.3f}, {aucs.max():.3f}]")
        ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=0.8)
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
        ax.set_title(f"{site.title()}", fontsize=12)
        ax.legend(loc="lower right", fontsize=9)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

        summary[site] = {
            "observed_auc": auc0,
            "n_boot": int(valid_runs.sum()),
            "auc_q025": float(np.percentile(aucs, 2.5)),
            "auc_q975": float(np.percentile(aucs, 97.5)),
            "auc_min_run": float(aucs.min()),
            "auc_max_run": float(aucs.max()),
        }
        print(f"  {site}: AUC={auc0:.3f}  CI=[{summary[site]['auc_q025']:.3f}, {summary[site]['auc_q975']:.3f}]")

    # Hide last unused subplot
    if len(SITES) < 6:
        axes[5].set_visible(False)

    fig.suptitle(f"PineSentry-Fire v1 - bootstrap 95% ROC envelope (N={N_BOOT}) across 5 sites",
                 fontsize=13, y=1.0)
    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    Path("data/hsi/v1/roc_envelope_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
