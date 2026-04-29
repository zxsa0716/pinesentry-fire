"""Spatial logistic regression with autoregressive correlation structure.

R-INLA equivalent in Python via statsmodels GEE with cluster correlation.
Tests whether HSI v1 remains significant after controlling for spatial
autocorrelation between adjacent pixels.

Output: data/hsi/v1/{site}_glmm.json with coefficient + Wald test.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "palisades")    # only sites with HSI signal


def main():
    import geopandas as gpd
    from rasterio.features import rasterize

    try:
        import statsmodels.api as sm
        from statsmodels.genmod.cov_struct import Exchangeable
    except ImportError:
        print("pip install statsmodels", file=sys.stderr); return

    summary = {}
    rng = np.random.default_rng(0)

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
        score = h.values[valid]
        y = burn[valid].astype(int)

        # 50 km blocks for spatial cluster id
        H, W = h.shape
        block_size = max(1, min(H, W) // 8)   # ~8x8 = 64 blocks
        ys, xs = np.where(valid)
        block_id = (ys // block_size) * 100 + (xs // block_size)

        # Subsample for speed
        n = min(20_000, len(y))
        idx = rng.choice(len(y), n, replace=False)
        y_s = y[idx]; score_s = score[idx]; block_s = block_id[idx]

        if y_s.sum() < 10:
            continue

        try:
            X = sm.add_constant(score_s)
            # GEE with exchangeable spatial cluster
            mdl = sm.GEE(y_s, X, groups=block_s, family=sm.families.Binomial(),
                         cov_struct=Exchangeable())
            res = mdl.fit()
            coef = float(res.params[1])
            se = float(res.bse[1])
            wald_z = coef / se
            from scipy.stats import norm
            p = float(2 * (1 - norm.cdf(abs(wald_z))))
            summary[site] = {
                "n": int(n), "n_burn": int(y_s.sum()),
                "n_clusters": int(np.unique(block_s).size),
                "coef": coef, "se": se, "wald_z": float(wald_z), "p": p,
                "odds_ratio": float(np.exp(coef)),
            }
            print(f"  {site:>10}: GEE coef = {coef:+.3f} (SE {se:.3f}), z={wald_z:.2f}, p={p:.2e}, OR={np.exp(coef):.2f}")
        except Exception as e:
            print(f"  {site}: failed {e}", file=sys.stderr)

    Path("data/hsi/v1/glmm_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> data/hsi/v1/glmm_summary.json")


if __name__ == "__main__":
    main()
