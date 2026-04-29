"""Per-site bootstrap uncertainty for HSI v1 AUC and lift.

Rather than perturbing weights (A6 already done), bootstrap the
burned/unburned pixel sample. Reports 95% CI per site.

Output: data/hsi/v1/{site}_bootstrap.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
N_BOOT = 200


def load_v1(site):
    p = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    if p.exists():
        return rxr.open_rasterio(p, masked=True).squeeze()
    return None


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score

    summary = {}
    rng = np.random.default_rng(42)

    for site in SITES:
        h = load_v1(site)
        if h is None:
            continue
        peri_path = Path(f"data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                    else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not peri_path.exists():
            continue
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]
        unburned = h.values[(~burn) & valid]
        if len(burned) < 50:
            print(f"  {site}: too few burned ({len(burned)}); skip bootstrap")
            continue

        # Sample (n_b, n_u) = min(burned, 5000) and same fraction unburned
        n_b = min(len(burned), 5000)
        n_u = min(len(unburned), 50000)
        aucs = []
        lifts = []
        for _ in range(N_BOOT):
            idx_b = rng.choice(len(burned), n_b, replace=True)
            idx_u = rng.choice(len(unburned), n_u, replace=True)
            sb = burned[idx_b]; su = unburned[idx_u]
            y = np.concatenate([np.ones(n_b), np.zeros(n_u)])
            s = np.concatenate([sb, su])
            try:
                aucs.append(roc_auc_score(y, s))
            except Exception:
                continue
            order = np.argsort(-s)
            top10 = order[: max(1, len(order) // 10)]
            lifts.append(y[top10].mean() / max(y.mean(), 1e-9))

        summary[site] = {
            "n_burned_total": int(len(burned)),
            "n_unburned_total": int(len(unburned)),
            "n_boot": N_BOOT,
            "auc_mean": float(np.mean(aucs)),
            "auc_q025": float(np.percentile(aucs, 2.5)),
            "auc_q975": float(np.percentile(aucs, 97.5)),
            "lift_mean": float(np.mean(lifts)),
            "lift_q025": float(np.percentile(lifts, 2.5)),
            "lift_q975": float(np.percentile(lifts, 97.5)),
        }
        s = summary[site]
        print(f"  {site:>10}: AUC = {s['auc_mean']:.3f} [95% CI {s['auc_q025']:.3f}-{s['auc_q975']:.3f}], "
              f"lift = {s['lift_mean']:.2f} [{s['lift_q025']:.2f}-{s['lift_q975']:.2f}]")

    out = Path("data/hsi/v1/bootstrap_summary.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
