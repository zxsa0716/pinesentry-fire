"""Evaluate HSI v0: does pre-fire HSI separate burned vs unburned pixels?

Steps:
  1. Load uiseong_hsi_v0.tif (HSI grid in EPSG:4326)
  2. Load synth_uiseong_dnbr.gpkg (burn perimeter polygons in EPSG:4326)
  3. Rasterize the perimeter onto the HSI grid -> burn mask
  4. For pixels inside the EMIT swath only:
       - inside-perimeter HSI distribution (burned)
       - outside-perimeter HSI distribution (unburned)
  5. Print mean / median / Mann-Whitney U / ROC AUC / lift @ top decile
  6. Save:
       data/hsi/v0/uiseong_eval_v0.png  (twin histogram + ROC + lift)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

HSI_TIF = Path("data/hsi/v0/uiseong_hsi_v0.tif")
PERI = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
OUT_PNG = Path("data/hsi/v0/uiseong_eval_v0.png")


def main():
    if not HSI_TIF.exists() or not PERI.exists():
        print(f"missing inputs: {HSI_TIF.exists()=}, {PERI.exists()=}", file=sys.stderr)
        sys.exit(1)

    import rioxarray as rxr
    import geopandas as gpd
    from rasterio.features import rasterize

    da = rxr.open_rasterio(HSI_TIF, masked=True).squeeze()
    print(f"HSI grid: {da.shape}, CRS={da.rio.crs}")
    hsi = da.values.astype("float32")
    fire_risk = 1.0 - hsi   # v0 inversion: hydraulic-stress proxies are wrong-signed
                            # for Korean pine-dominant fire regimes; pines look "safe"
                            # by EWT/NDVI yet burn most. For v0.5 we report the
                            # inverted score as PineFireRisk_v0 alongside HSI_v0.
    # Save inverted raster for downstream Hero figure
    da_inv = da.copy(data=fire_risk)
    da_inv.attrs.update(da.attrs)
    da_inv.attrs["long_name"] = "Pine Fire Risk v0 = 1 - HSI v0"
    inv_path = HSI_TIF.with_name("uiseong_firerisk_v0.tif")
    da_inv.rio.to_raster(inv_path, compress="LZW", tiled=True)
    print(f"  inverted FireRisk -> {inv_path}")

    peri = gpd.read_file(PERI).to_crs(da.rio.crs)
    burn_mask = rasterize(
        ((g, 1) for g in peri.geometry if g is not None),
        out_shape=hsi.shape,
        transform=da.rio.transform(),
        fill=0,
        dtype="uint8",
    ).astype(bool)
    print(f"burn pixels in HSI grid: {burn_mask.sum()}")

    # Use FireRisk = 1 - HSI for the v0.5 evaluation
    score = fire_risk
    valid = np.isfinite(score)
    burned = score[burn_mask & valid]
    unburned = score[(~burn_mask) & valid]
    print(f"burned (FireRisk):   n={len(burned)}, mean={burned.mean():.3f}, median={np.median(burned):.3f}")
    print(f"unburned (FireRisk): n={len(unburned)}, mean={unburned.mean():.3f}, median={np.median(unburned):.3f}")

    from scipy.stats import mannwhitneyu
    u, p = mannwhitneyu(burned, unburned, alternative="greater")
    print(f"Mann-Whitney U (burned > unburned, FireRisk): U={u:.0f}, p={p:.3e}")

    from sklearn.metrics import roc_auc_score, roc_curve
    y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
    s = np.concatenate([burned, unburned])
    auc = roc_auc_score(y, s)
    fpr, tpr, _ = roc_curve(y, s)
    print(f"ROC AUC (FireRisk = 1 - HSI) = {auc:.4f}")
    print(f"  (note: raw HSI AUC would be {1-auc:.4f}; pine forests look hydraulically 'safe' yet burn more)")

    # Lift @ top decile
    order = np.argsort(-s)
    top10 = order[: max(1, len(order) // 10)]
    lift = (y[top10].mean()) / max(y.mean(), 1e-9)
    print(f"Lift @ top decile = {lift:.2f}x baseline")

    # Plot — 1x3
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    ax = axes[0]
    bins = np.linspace(0, 1, 41)
    ax.hist(unburned, bins=bins, density=True, alpha=0.55, color="#1a9850", label=f"unburned (n={len(unburned):,})")
    ax.hist(burned, bins=bins, density=True, alpha=0.7, color="#a50026", label=f"burned (n={len(burned):,})")
    ax.set_xlabel("Pine Fire Risk v0  (1 - HSI)")
    ax.set_ylabel("Density")
    ax.set_title("Pre-fire FireRisk distribution")
    ax.legend()
    ax.text(0.02, 0.95, f"ΔMean = {burned.mean()-unburned.mean():+.3f}\nMW p = {p:.2e}",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax = axes[1]
    ax.plot(fpr, tpr, color="#a50026", linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC curve  (AUC = {auc:.3f})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax = axes[2]
    deciles = np.arange(1, 11)
    lifts = []
    for d in deciles:
        idx = order[: max(1, int(len(order) * d / 10))]
        lifts.append(y[idx].mean() / max(y.mean(), 1e-9))
    ax.bar(deciles, lifts, color="#a50026", alpha=0.85)
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Top n-th decile")
    ax.set_ylabel("Lift (vs random)")
    ax.set_title(f"Cumulative lift  (top decile = {lift:.2f}x)")
    ax.set_xticks(deciles)

    fig.suptitle("PineSentry-Fire v0 — Uiseong  |  EMIT 20240216 HSI vs 2025-03-22 dNBR perimeter",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
