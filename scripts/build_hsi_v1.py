"""HSI v1 — multi-layer fire-risk score.

Combines:
  - FireRisk v0 (1 - HSI_v0 empirical)        — captures species-EWT signal
  - Pyrophilic factor (species-specific)       — pine resin/wax → flammable
  - South-facing slope                         — solar exposure / drying
  - Pine fraction                              — explicit pine binary
  - HSI v1 = w1*pyro + w2*south + w3*firerisk_v0 + w4*pine_terrain

Weights are physiologically motivated (not data-fit on Uiseong):
  w_pyro     = 0.40   (species drives K-fire regime)
  w_south    = 0.20   (terrain dries fuel)
  w_firerisk = 0.30   (the v0 hyperspectral signal)
  w_pine_tx  = 0.10   (interaction = pyrophilic * south)

Then evaluate on the dNBR perimeter same as v0.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import rioxarray as rxr
import xarray as xr

ROI = sys.argv[1] if len(sys.argv) > 1 else "uiseong"
STACK = Path(f"data/features/{ROI}_stack.tif")
PERI = Path(f"data/fire_perimeter/synth_{ROI}_dnbr.gpkg")
OUT_DIR = Path("data/hsi/v1")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WEIGHTS = {"pyro": 0.40, "south": 0.20, "firerisk": 0.30, "pine_tx": 0.10}


def percentile_norm(arr: np.ndarray, lo=5, hi=95) -> np.ndarray:
    m = np.isfinite(arr)
    if m.sum() < 10:
        return np.zeros_like(arr)
    plo, phi = np.nanpercentile(arr[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(arr)
    return np.clip((arr - plo) / (phi - plo), 0, 1)


def main():
    if not STACK.exists():
        print(f"Need feature stack: {STACK}", file=sys.stderr)
        sys.exit(1)

    da = rxr.open_rasterio(STACK, masked=True)
    bands = list(da.coords["band"].values) if "band" in da.coords else None
    print(f"Stack shape: {da.shape}, CRS={da.rio.crs}")

    arr = da.values   # shape (10, H, W)
    # Per build_feature_stack.py band order
    hsi_v0       = arr[0]
    firerisk_v0  = arr[1]
    elev         = arr[2]
    slope        = arr[3]
    aspect       = arr[4]
    south_face   = arr[5]
    pyro         = arr[6]
    pine_frac    = arr[7]
    worldcover   = arr[8]
    pine_terrain = arr[9]

    # Forest mask: pyrophilic > 0 already encodes "is forest" via imsangdo,
    # so we keep all pixels with finite firerisk_v0.
    valid_mask = np.isfinite(firerisk_v0)

    pyro_n     = percentile_norm(pyro)
    south_n    = percentile_norm(south_face)
    fr_n       = percentile_norm(firerisk_v0)
    tx_n       = percentile_norm(pine_terrain)

    hsi_v1 = (
        WEIGHTS["pyro"]     * pyro_n +
        WEIGHTS["south"]    * south_n +
        WEIGHTS["firerisk"] * fr_n +
        WEIGHTS["pine_tx"]  * tx_n
    )
    hsi_v1 = np.where(valid_mask, hsi_v1, np.nan)
    print(f"  HSI v1 distribution: " + " ".join(f"p{p}={np.nanpercentile(hsi_v1, p):.2f}" for p in [5, 25, 50, 75, 95]))

    out_tif = OUT_DIR / f"{ROI}_hsi_v1.tif"
    da_out = xr.DataArray(
        hsi_v1.astype("float32"), dims=("y", "x"),
        coords={"y": da.y, "x": da.x},
        name="hsi_v1",
    )
    da_out.attrs.update({
        "weights": str(WEIGHTS),
        "components": "0.4*pyro + 0.2*south + 0.3*firerisk_v0 + 0.1*pine_terrain (forest mask)",
    })
    da_out.rio.write_crs(da.rio.crs, inplace=True)
    da_out.rio.to_raster(out_tif, compress="LZW", tiled=True)
    print(f"  HSI v1 -> {out_tif}")

    # ----- Evaluate against dNBR perimeter -----
    if not PERI.exists():
        print(f"No perimeter to evaluate against: {PERI}")
        return
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve
    from scipy.stats import mannwhitneyu

    peri = gpd.read_file(PERI).to_crs(da.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=hsi_v1.shape,
                     transform=da.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(hsi_v1)
    burned = hsi_v1[burn & valid]
    unburned = hsi_v1[(~burn) & valid]
    print(f"\n  burned:   n={len(burned)}, mean={np.mean(burned):.3f}")
    print(f"  unburned: n={len(unburned)}, mean={np.mean(unburned):.3f}")
    if len(burned) and len(unburned):
        u, p = mannwhitneyu(burned, unburned, alternative="greater")
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        auc = roc_auc_score(y, s)
        order = np.argsort(-s)
        top10 = order[: max(1, len(order) // 10)]
        lift = (y[top10].mean()) / max(y.mean(), 1e-9)
        print(f"\n  HSI v1 ROC AUC = {auc:.4f}    (v0 was 0.6970)")
        print(f"  HSI v1 top-decile lift = {lift:.2f}x   (v0 was 2.32x)")
        print(f"  Mann-Whitney p = {p:.2e}")

        # ----- Save evaluation PNG -----
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fpr, tpr, _ = roc_curve(y, s)
        deciles = np.arange(1, 11)
        lifts = [y[order[: max(1, int(len(order) * d / 10))]].mean() / max(y.mean(), 1e-9) for d in deciles]

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        ax = axes[0]
        bins = np.linspace(0, 1, 41)
        ax.hist(unburned, bins=bins, density=True, alpha=0.55, color="#1a9850", label=f"unburned (n={len(unburned):,})")
        ax.hist(burned, bins=bins, density=True, alpha=0.7, color="#a50026", label=f"burned (n={len(burned):,})")
        ax.set_xlabel("HSI v1  (multi-layer)")
        ax.set_ylabel("Density")
        ax.set_title("Pre-fire HSI v1 distribution")
        ax.legend()
        ax.text(0.02, 0.95, f"ΔMean = {np.mean(burned)-np.mean(unburned):+.3f}\nMW p = {p:.2e}",
                transform=ax.transAxes, va="top", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

        ax = axes[1]
        ax.plot(fpr, tpr, color="#a50026", linewidth=2)
        ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title(f"ROC v1 (AUC = {auc:.3f})  vs v0 (0.697)")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

        ax = axes[2]
        ax.bar(deciles, lifts, color="#a50026", alpha=0.85, label="v1")
        ax.axhline(1.0, color="grey", linestyle="--", linewidth=1)
        ax.set_xlabel("Top n-th decile")
        ax.set_ylabel("Lift (vs random)")
        ax.set_title(f"Cumulative lift v1 (top decile = {lift:.2f}x)")
        ax.set_xticks(deciles)

        fig.suptitle(f"PineSentry-Fire v1 — {ROI.title()}  |  multi-layer fire-risk vs dNBR perimeter", fontsize=12, y=1.02)
        fig.tight_layout()
        eval_png = OUT_DIR / f"{ROI}_eval_v1.png"
        fig.savefig(eval_png, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  v1 eval PNG -> {eval_png}")


if __name__ == "__main__":
    main()
