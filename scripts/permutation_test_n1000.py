"""Permutation test at N=1000 (v4.1 explicit spec — extends N=500 default).

Identical to permutation_test.py but with N=1000 shuffles for the
v4.1 design's stated 1000 shuffles (we previously ran N=500).
The p-value precision improves from 1/500=0.002 to 1/1000=0.001.

Output: data/hsi/v1/permutation_summary_n1000.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
N_PERM = 1000


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(42)
    summary = {}

    for site in SITES:
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        if not h_path.exists():
            continue
        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                    else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not peri_path.exists():
            continue
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]; unburned = h.values[(~burn) & valid]
        if len(burned) < 10:
            continue

        n_b = min(len(burned), 5000)
        n_u = min(len(unburned), 50000)
        idx_b = rng.choice(len(burned), n_b, replace=False)
        idx_u = rng.choice(len(unburned), n_u, replace=False)
        sb = burned[idx_b]; su = unburned[idx_u]
        y = np.concatenate([np.ones(n_b), np.zeros(n_u)])
        s = np.concatenate([sb, su])
        observed_auc = roc_auc_score(y, s)

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
            "p_value_text": f"< 1/{N_PERM}" if p_value == 0 else f"{p_value:.4f}",
        }
        print(f"  {site:>10}: AUC = {observed_auc:.4f}, null = {null_aucs.mean():.3f}+/-{null_aucs.std():.3f}, p = {summary[site]['p_value_text']}")

    Path("data/hsi/v1/permutation_summary_n1000.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> data/hsi/v1/permutation_summary_n1000.json")


if __name__ == "__main__":
    main()
