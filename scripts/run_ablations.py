"""HSI v1 component ablation — drop each one and report AUC delta.

Components in HSI v1 = 0.40 pyro + 0.20 south + 0.30 firerisk + 0.10 pine_tx

A1: drop pyrophilic                    -> redistribute 0.40 to others
A2: drop south_facing                  -> redistribute 0.20
A3: drop firerisk_v0 (EMIT empirical)  -> redistribute 0.30
A4: drop pine_terrain interaction      -> redistribute 0.10
A_full: keep all (baseline = v1 0.747 / 0.647)

Output: data/hsi/v1/ablations_summary.json + ablations_chart.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT_DIR = Path("data/hsi/v1")

W = {"pyro": 0.40, "south": 0.20, "firerisk": 0.30, "pine_tx": 0.10}


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def evaluate(score, peri_path, h_grid):
    if not peri_path.exists():
        return None
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score
    peri = gpd.read_file(peri_path).to_crs(h_grid.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=score.shape, transform=h_grid.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(score)
    burned = score[burn & valid]; unburned = score[(~burn) & valid]
    if len(burned) < 5 or len(unburned) < 5:
        return None
    y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
    s = np.concatenate([burned, unburned])
    return float(roc_auc_score(y, s))


def run_site(site):
    stack = Path(f"data/features/{site}_stack.tif")
    if not stack.exists():
        print(f"  no feature stack {site}"); return None
    da = rxr.open_rasterio(stack, masked=True)
    bands = da.values
    pyro = bands[6]; south = bands[5]; firerisk = bands[1]; pine_tx = bands[9]
    grid = da.sel(band=1)
    peri = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")

    pyro_n = percentile_norm(pyro); south_n = percentile_norm(south)
    fr_n = percentile_norm(firerisk); tx_n = percentile_norm(pine_tx)

    scenarios = {
        "A_full":     {"pyro": W["pyro"], "south": W["south"], "firerisk": W["firerisk"], "pine_tx": W["pine_tx"]},
        "A1_no_pyro": {"south": W["south"]+0.13, "firerisk": W["firerisk"]+0.20, "pine_tx": W["pine_tx"]+0.07},
        "A2_no_south":{"pyro": W["pyro"]+0.07, "firerisk": W["firerisk"]+0.10, "pine_tx": W["pine_tx"]+0.03},
        "A3_no_firerisk":{"pyro": W["pyro"]+0.15, "south": W["south"]+0.10, "pine_tx": W["pine_tx"]+0.05},
        "A4_no_pinetx":{"pyro": W["pyro"]+0.05, "south": W["south"]+0.025, "firerisk": W["firerisk"]+0.025},
    }
    norms = {"pyro": pyro_n, "south": south_n, "firerisk": fr_n, "pine_tx": tx_n}
    results = {}
    for name, w in scenarios.items():
        score = sum(w.get(k, 0) * norms[k] for k in norms)
        auc = evaluate(score, peri, grid)
        if auc is not None:
            results[name] = auc
            print(f"  {site} {name:>14}: AUC = {auc:.4f}")
    return results


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for site in ("uiseong", "sancheong"):
        print(f"\n=== {site} ===")
        r = run_site(site)
        if r:
            summary[site] = r
    (OUT_DIR / "ablations_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT_DIR / 'ablations_summary.json'}")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    sites = list(summary.keys())
    scenarios = ["A_full", "A1_no_pyro", "A2_no_south", "A3_no_firerisk", "A4_no_pinetx"]
    width = 0.35
    x = np.arange(len(scenarios))
    colors = {"uiseong": "#a50026", "sancheong": "#313695"}
    for i, s in enumerate(sites):
        vals = [summary[s].get(sc, np.nan) for sc in scenarios]
        offset = (i - len(sites)/2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width, color=colors.get(s, "k"), alpha=0.85, label=s.title())
        for b, v in zip(bars, vals):
            if np.isfinite(v):
                ax.text(b.get_x() + b.get_width()/2, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(["full v1", "no pyro", "no south", "no firerisk", "no pine_tx"], rotation=15)
    ax.set_ylabel("ROC AUC")
    ax.set_title("HSI v1 component ablation — AUC vs leave-one-out")
    ax.legend(); ax.set_ylim(0.45, 0.85)
    fig.tight_layout()
    out_png = OUT_DIR / "ablations_chart.png"
    fig.savefig(out_png, dpi=140, bbox_inches="tight"); plt.close(fig)
    print(f"saved -> {out_png}")


if __name__ == "__main__":
    main()
