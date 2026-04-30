"""Case-control 1:5 sampling (Phillips & Elith 2013) per v4.1 §2.3.

Phillips & Elith 2013 propose case-control sampling for presence-absence
ecology to reduce bias from severe class imbalance. We implement 1:5
(unburned : burned) sampling for HSI v1 evaluation across all 5 sites
and report AUC under this design vs the all-pixels design we used.

Output: data/hsi/v1/case_control_summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")


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
        if site == "palisades":
            peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson")
        else:
            peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not peri_path.exists():
            continue
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)

        scores_all = h.values[valid]
        burn_all = burn[valid]
        n_burn = int(burn_all.sum())
        n_unburn = int((~burn_all).sum())
        if n_burn < 5 or n_unburn < 5:
            continue

        # All-pixels AUC (baseline reported earlier)
        auc_all = float(roc_auc_score(burn_all.astype(int), scores_all))

        # Case-control: keep all burn pixels, sample 5x as many unburn
        burn_idx = np.where(burn_all)[0]
        unburn_idx = np.where(~burn_all)[0]
        n_take = min(5 * n_burn, len(unburn_idx))
        n_runs = 100
        aucs_cc = []
        for _ in range(n_runs):
            ui = rng.choice(unburn_idx, n_take, replace=False)
            sub = np.concatenate([burn_idx, ui])
            try:
                a = roc_auc_score(burn_all[sub].astype(int), scores_all[sub])
                aucs_cc.append(a)
            except Exception:
                pass
        aucs_cc = np.array(aucs_cc)

        summary[site] = {
            "n_burn": n_burn, "n_unburn_total": n_unburn,
            "n_unburn_kept_per_run": n_take,
            "auc_all_pixels": auc_all,
            "auc_case_control_1to5_mean": float(aucs_cc.mean()),
            "auc_case_control_1to5_std": float(aucs_cc.std()),
            "auc_case_control_q025": float(np.quantile(aucs_cc, 0.025)),
            "auc_case_control_q975": float(np.quantile(aucs_cc, 0.975)),
        }
        print(f"  {site}: all-pixels AUC={auc_all:.4f} | case-control 1:5 "
              f"mean={aucs_cc.mean():.4f} 95%CI=[{np.quantile(aucs_cc,0.025):.4f}, {np.quantile(aucs_cc,0.975):.4f}]")

    Path("data/hsi/v1/case_control_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> data/hsi/v1/case_control_summary.json")


if __name__ == "__main__":
    main()
