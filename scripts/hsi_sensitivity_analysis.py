"""HSI v1 weight-sensitivity analysis (A6 ablation).

Perturbs the four locked weights by ±20% and reports per-site AUC range.
Confirms whether the result depends on the exact weight choice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

W_DEFAULT = {"pyro": 0.40, "south": 0.20, "firerisk": 0.30, "pine_tx": 0.10}


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def evaluate(hsi, peri_path, h_grid):
    if not peri_path.exists():
        return None
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score
    peri = gpd.read_file(peri_path).to_crs(h_grid.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=hsi.shape, transform=h_grid.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(hsi)
    burned = hsi[burn & valid]; unburned = hsi[(~burn) & valid]
    if len(burned) < 5 or len(unburned) < 5:
        return None
    y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
    s = np.concatenate([burned, unburned])
    return float(roc_auc_score(y, s))


def run_site(site, n_samples=64):
    stack_path = Path(f"data/features/{site}_stack.tif")
    if not stack_path.exists():
        print(f"  no feature stack for {site}"); return None
    da = rxr.open_rasterio(stack_path, masked=True)
    bands = da.values
    pyro = bands[6]; pine_frac = bands[7]; south = bands[5]; firerisk = bands[1]
    pine_tx = pyro * south

    pyro_n = percentile_norm(pyro)
    south_n = percentile_norm(south)
    fr_n = percentile_norm(firerisk)
    tx_n = percentile_norm(pine_tx)

    h_grid = da.sel(band=1)
    peri = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
    rng = np.random.default_rng(42)
    aucs = []
    deltas = []
    base = np.array([W_DEFAULT[k] for k in ("pyro", "south", "firerisk", "pine_tx")])
    for _ in range(n_samples):
        delta = rng.uniform(-0.20, 0.20, size=4) * base
        w = np.clip(base + delta, 0.01, None)
        w = w / w.sum()
        h = w[0] * pyro_n + w[1] * south_n + w[2] * fr_n + w[3] * tx_n
        auc = evaluate(h, peri, h_grid)
        if auc is not None:
            aucs.append(auc)
            deltas.append(w.tolist())

    if aucs:
        out = {
            "site": site,
            "n_samples": n_samples,
            "auc_mean": float(np.mean(aucs)),
            "auc_std": float(np.std(aucs)),
            "auc_min": float(np.min(aucs)),
            "auc_max": float(np.max(aucs)),
            "auc_median": float(np.median(aucs)),
            "auc_q05": float(np.percentile(aucs, 5)),
            "auc_q95": float(np.percentile(aucs, 95)),
            "default_weights": W_DEFAULT,
            "perturbation_pct": 20,
        }
        path = Path(f"data/hsi/v1/{site}_sensitivity.json")
        path.write_text(json.dumps(out, indent=2))
        print(f"  {site} sensitivity (±20% perturb, n={n_samples}):")
        print(f"    AUC mean = {out['auc_mean']:.3f} ± {out['auc_std']:.3f}")
        print(f"    AUC 5-95% range = [{out['auc_q05']:.3f}, {out['auc_q95']:.3f}]")
        print(f"    saved -> {path}")
        return out


def main():
    for site in ("uiseong", "sancheong"):
        print(f"\n=== {site} ===")
        run_site(site)


if __name__ == "__main__":
    main()
