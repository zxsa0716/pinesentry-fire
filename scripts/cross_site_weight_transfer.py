"""Cross-site weight-transfer test.

Fit HSI component weights on Uiseong burn labels via L2-regularized logistic
regression, then *freeze* and apply identically to Sancheong. Reports the
AUC delta vs the OSF-pre-registered (0.40 / 0.20 / 0.30 / 0.10) weights.

If Uiseong-tuned weights ≈ OSF-pre-registered weights AND give good
Sancheong AUC, the OSF weights are validated as transferable.
If Uiseong-tuned weights deviate AND give worse Sancheong AUC, that
falsifies the cross-site claim.

Output: data/hsi/v1/cross_site_transfer.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

OSF_W = np.array([0.40, 0.20, 0.30, 0.10])
LABELS = ["pyro", "south", "firerisk", "pine_terrain"]


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def features_and_y(site):
    import geopandas as gpd
    from rasterio.features import rasterize

    stack = rxr.open_rasterio(Path(f"data/features/{site}_stack.tif"), masked=True)
    pyro = stack.values[6]; south = stack.values[5]
    # Use stack-derived NDII/NDVI proxy directly (always shape-matched)
    ndii_n = percentile_norm(stack.values[1])
    ndvi_n = percentile_norm(stack.values[0])
    fr_v0 = 0.6 * (1 - ndii_n) + 0.4 * (1 - ndvi_n)
    pine_tx = pyro * south

    F = np.stack([percentile_norm(pyro), percentile_norm(south),
                  percentile_norm(fr_v0), percentile_norm(pine_tx)], axis=-1)

    peri = gpd.read_file(f"data/fire_perimeter/synth_{site}_dnbr.gpkg").to_crs(stack.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=stack.shape[1:], transform=stack.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.all(np.isfinite(F), axis=-1)
    return F[valid], burn[valid].astype(int)


def main():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    print("Loading Uiseong (training) ...")
    F_u, y_u = features_and_y("uiseong")
    print(f"  Uiseong: n={len(y_u)}, n_burn={y_u.sum()}")

    print("Loading Sancheong (held-out) ...")
    F_s, y_s = features_and_y("sancheong")
    print(f"  Sancheong: n={len(y_s)}, n_burn={y_s.sum()}")

    # Subsample for speed (Uiseong has 350K pixels)
    rng = np.random.default_rng(0)
    n_train = min(50000, len(y_u))
    idx = rng.choice(len(y_u), n_train, replace=False)
    Ftr, ytr = F_u[idx], y_u[idx]

    # L2 logistic, force POSITIVE coefficients via constraint approximation:
    # Train unrestricted, then if any coef < 0 we report it (and also report
    # weighted-sum at OSF weights for comparison).
    clf = LogisticRegression(C=1.0, max_iter=2000)
    clf.fit(Ftr, ytr)
    coefs = clf.coef_.ravel()
    coefs_norm = np.clip(coefs, 0, None)
    coefs_norm = coefs_norm / (coefs_norm.sum() + 1e-9)
    print(f"\nUiseong-fit raw logit coefs: {dict(zip(LABELS, coefs.round(4)))}")
    print(f"Uiseong-fit clipped+normed:   {dict(zip(LABELS, coefs_norm.round(4)))}")
    print(f"OSF-pre-registered weights:   {dict(zip(LABELS, OSF_W))}")

    # Apply both sets of weights to BOTH sites
    rows = []
    for site, F, y in [("uiseong", F_u, y_u), ("sancheong", F_s, y_s)]:
        s_osf = (F * OSF_W[None, :]).sum(axis=-1)
        s_fit = (F * coefs_norm[None, :]).sum(axis=-1)
        try:
            auc_osf = float(roc_auc_score(y, s_osf))
            auc_fit = float(roc_auc_score(y, s_fit))
        except Exception:
            auc_osf = auc_fit = None
        rows.append({"site": site, "auc_OSF": auc_osf, "auc_Uiseongfit": auc_fit, "delta": (auc_fit - auc_osf) if auc_osf else None})
        print(f"  {site}: OSF AUC={auc_osf:.4f}  Uiseongfit AUC={auc_fit:.4f}  delta={rows[-1]['delta']:+.4f}")

    Path("data/hsi/v1/cross_site_transfer.json").write_text(json.dumps({
        "OSF_weights": OSF_W.tolist(),
        "Uiseong_logit_coefs_raw": coefs.tolist(),
        "Uiseong_logit_coefs_normed": coefs_norm.tolist(),
        "labels": LABELS,
        "rows": rows,
    }, indent=2))
    print("\nsaved -> data/hsi/v1/cross_site_transfer.json")


if __name__ == "__main__":
    main()
