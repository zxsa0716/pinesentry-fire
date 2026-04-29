"""Spatial-block cross-validation for HSI v1 weights — robustness check.

Spatial autocorrelation in burn pixels means a random-pixel CV would
over-estimate AUC. We split each site into N×N tiles and hold one tile
out at a time.

Output: data/hsi/v1/{site}_spatial_cv.json with per-fold AUC stats.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITE = sys.argv[1] if len(sys.argv) > 1 else "uiseong"
N_BLOCKS = int(sys.argv[2]) if len(sys.argv) > 2 else 4    # 4x4 = 16 blocks


def main():
    hsi_path = Path(f"data/hsi/v1/{SITE}_hsi_v1.tif")
    peri_path = Path(f"data/fire_perimeter/synth_{SITE}_dnbr.gpkg")
    if not hsi_path.exists() or not peri_path.exists():
        print(f"missing inputs", file=sys.stderr); sys.exit(1)

    da = rxr.open_rasterio(hsi_path, masked=True).squeeze()
    H, W = da.shape
    print(f"HSI grid {H}x{W}, splitting into {N_BLOCKS}x{N_BLOCKS} blocks")

    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score

    peri = gpd.read_file(peri_path).to_crs(da.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=(H, W),
                     transform=da.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)

    score = da.values
    aucs = []
    folds = []
    by = H // N_BLOCKS
    bx = W // N_BLOCKS
    for j in range(N_BLOCKS):
        for i in range(N_BLOCKS):
            y0, y1 = j * by, (j + 1) * by if j < N_BLOCKS - 1 else H
            x0, x1 = i * bx, (i + 1) * bx if i < N_BLOCKS - 1 else W
            test = np.zeros((H, W), dtype=bool)
            test[y0:y1, x0:x1] = True
            burn_t = burn & test
            unburn_t = (~burn) & test
            valid = np.isfinite(score) & test
            burned_s = score[burn_t & valid]
            unburned_s = score[unburn_t & valid]
            if len(burned_s) < 5 or len(unburned_s) < 5:
                continue
            y = np.concatenate([np.ones(len(burned_s)), np.zeros(len(unburned_s))])
            s = np.concatenate([burned_s, unburned_s])
            try:
                auc = roc_auc_score(y, s)
                aucs.append(auc)
                folds.append({"block": (j, i), "n_burn": int(len(burned_s)), "n_unburn": int(len(unburned_s)), "auc": float(auc)})
            except Exception:
                pass

    if aucs:
        out = {
            "site": SITE,
            "n_blocks": N_BLOCKS * N_BLOCKS,
            "n_folds_with_signal": len(aucs),
            "auc_mean": float(np.mean(aucs)),
            "auc_std": float(np.std(aucs)),
            "auc_min": float(np.min(aucs)),
            "auc_max": float(np.max(aucs)),
            "auc_median": float(np.median(aucs)),
            "folds": folds,
        }
        path = Path(f"data/hsi/v1/{SITE}_spatial_cv.json")
        path.write_text(json.dumps(out, indent=2))
        print(f"\n{SITE} spatial-block CV ({len(aucs)} folds with signal of {N_BLOCKS*N_BLOCKS}):")
        print(f"  AUC mean = {out['auc_mean']:.3f} +/- {out['auc_std']:.3f}")
        print(f"  AUC range = [{out['auc_min']:.3f}, {out['auc_max']:.3f}]")
        print(f"  AUC median = {out['auc_median']:.3f}")
        print(f"  saved -> {path}")


if __name__ == "__main__":
    main()
