"""Moran's I spatial autocorrelation diagnostic on HSI v1 residuals.

Confirms / corroborates the GEE Wald test. Computes Moran's I on:
  (a) the burn-label field y in {0, 1}
  (b) the residual r = y - logistic(HSI v1 score)

If Moran's I of (a) is large positive (clustered burning) but (b) is near
zero, then HSI v1 has captured the spatial signal and the remaining
unexplained variation is approximately white noise.

Uses Queen contiguity (8 nearest neighbors) on a regular raster grid via
a sparse weights matrix subsample (5,000 points) for speed.

Output: data/hsi/v1/morans_i.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "palisades")


def morans_i_subset(values, coords, k=8, n_perm=99, rng=None):
    """Spatial Moran's I with k-nearest-neighbor weights on point subset."""
    from scipy.spatial import cKDTree
    rng = rng or np.random.default_rng(0)
    tree = cKDTree(coords)
    _, idx = tree.query(coords, k=k + 1)   # first neighbor is self
    idx = idx[:, 1:]
    n = len(values)
    z = values - values.mean()
    s2 = (z ** 2).sum()
    if s2 == 0:
        return None
    W = 0.0
    num = 0.0
    for i in range(n):
        for j in idx[i]:
            num += z[i] * z[j]
            W += 1.0
    if W == 0:
        return None
    I = (n / W) * (num / s2)

    # Random permutation null
    perm_I = []
    for _ in range(n_perm):
        zp = rng.permutation(z)
        num_p = 0.0
        for i in range(n):
            for j in idx[i]:
                num_p += zp[i] * zp[j]
        perm_I.append((n / W) * (num_p / s2))
    perm_I = np.array(perm_I)
    p_val = (np.sum(np.abs(perm_I) >= np.abs(I)) + 1) / (n_perm + 1)
    return {
        "I": float(I),
        "n_points": int(n),
        "n_neighbors": int(k),
        "p_perm": float(p_val),
        "perm_I_mean": float(perm_I.mean()),
        "perm_I_std": float(perm_I.std()),
    }


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
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
        ys, xs = np.where(valid)
        H = h.values
        score = H[valid]
        y = burn[valid].astype(float)

        # Subsample 4000 valid pixels uniformly
        n = min(4000, len(y))
        idx = rng.choice(len(y), n, replace=False)
        py = y[idx]; ps = score[idx]
        coords = np.column_stack([xs[idx], ys[idx]]).astype(float)

        # Logistic-fit residual to remove HSI v1 mean signal
        from scipy.special import expit
        # Centered, scaled score
        sx = (ps - ps.mean()) / (ps.std() + 1e-9)
        # MLE of logistic with Newton's method (1 covariate)
        # b = (Σ (y - p) sx) / (Σ p(1-p) sx²)
        b = 0.0
        for _ in range(15):
            p = expit(b * sx)
            grad = ((py - p) * sx).sum()
            hess = (p * (1 - p) * sx * sx).sum()
            if hess < 1e-9: break
            b += grad / hess
        p_fit = expit(b * sx)
        residual = py - p_fit

        I_y = morans_i_subset(py, coords, k=8, n_perm=99, rng=rng)
        I_r = morans_i_subset(residual, coords, k=8, n_perm=99, rng=rng)
        summary[site] = {"burn_label": I_y, "residual_after_HSI": I_r,
                         "logit_slope_b_sx": float(b)}
        print(f"  {site}: I(y)={I_y['I']:.3f} (p={I_y['p_perm']:.3f}); "
              f"I(residual)={I_r['I']:.3f} (p={I_r['p_perm']:.3f})")

    Path("data/hsi/v1/morans_i.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> data/hsi/v1/morans_i.json")


if __name__ == "__main__":
    main()
