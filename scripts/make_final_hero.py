"""Final Hero figure — 6-panel for the August submission and README.

Layout:
  Row 1: 의성 HSI v1 map + dNBR overlay  |  산청 HSI v1 map + dNBR overlay
  Row 2: ROC curves (의성 + 산청)           |  AUC bar chart (HSI v1 vs NDVI/NDMI/NDII × 2 sites)
  Row 3: Lift chart (의성 + 산청)            |  Two-site decile lift comparison
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT = Path("data/hsi/v1/HERO_final.png")
SITES = ("uiseong", "sancheong")


def load_sites():
    data = {}
    for site in SITES:
        hsi_v1 = rxr.open_rasterio(f"data/hsi/v1/{site}_hsi_v1.tif", masked=True).squeeze()
        try:
            import geopandas as gpd
            peri = gpd.read_file(f"data/fire_perimeter/synth_{site}_dnbr.gpkg").to_crs(hsi_v1.rio.crs)
        except Exception:
            peri = None
        summary = json.loads(Path(f"data/baselines/{site}_summary.json").read_text())
        data[site] = {"hsi": hsi_v1, "peri": peri, "summary": summary}
    return data


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = load_sites()

    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25)

    cmap = "YlOrRd"

    # ---- Row 1: HSI v1 maps + dNBR overlay ----
    for i, site in enumerate(SITES):
        ax = fig.add_subplot(gs[0, i])
        d = data[site]
        h = d["hsi"]
        extent = list(h.rio.bounds())
        # rio bounds: (left, bottom, right, top) -> imshow extent (left, right, bottom, top)
        im = ax.imshow(h.values, origin="upper", cmap=cmap,
                       extent=[extent[0], extent[2], extent[1], extent[3]],
                       vmin=0, vmax=1)
        if d["peri"] is not None:
            d["peri"].boundary.plot(ax=ax, edgecolor="black", linewidth=1.5)
            d["peri"].plot(ax=ax, facecolor="black", alpha=0.15)
        ax.set_title(f"{site.title()}  |  HSI v1 + dNBR perimeter", fontsize=12)
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="HSI v1")

    # ---- Row 2 left: ROC curves both sites + HSI v1 vs all baselines ----
    # We need fpr/tpr from raw data; for simplicity load baselines summary again.
    # The summary doesn't have fpr/tpr; rerun a quick eval here.
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve

    ax = fig.add_subplot(gs[1, 0])
    colors = {"uiseong": "#a50026", "sancheong": "#313695"}
    for site in SITES:
        d = data[site]
        h = d["hsi"].values.astype("float32")
        if d["peri"] is None:
            continue
        burn = rasterize(((g, 1) for g in d["peri"].geometry if g is not None),
                         out_shape=h.shape,
                         transform=d["hsi"].rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h)
        burned = h[burn & valid]
        unburned = h[(~burn) & valid]
        if len(burned) == 0:
            continue
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        auc = roc_auc_score(y, s)
        fpr, tpr, _ = roc_curve(y, s)
        ax.plot(fpr, tpr, color=colors[site], linewidth=2,
                label=f"{site.title()}  AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("HSI v1 ROC — both sites, identical weights", fontsize=12)
    ax.legend(loc="lower right")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # ---- Row 2 right: AUC bar chart by site × method ----
    ax = fig.add_subplot(gs[1, 1])
    methods = ["NDVI", "NDMI", "NDII", "HSI_v1"]
    method_colors = {"NDVI": "#fc8d59", "NDMI": "#74add1", "NDII": "#984ea3", "HSI_v1": "#a50026"}
    width = 0.35
    x = np.arange(len(methods))
    aucs_uiseong = [data["uiseong"]["summary"][m]["auc"] for m in methods]
    aucs_sancheong = [data["sancheong"]["summary"][m]["auc"] for m in methods]
    ax.bar(x - width/2, aucs_uiseong, width, color="#fc8d59", alpha=0.85, label="Uiseong")
    ax.bar(x + width/2, aucs_sancheong, width, color="#313695", alpha=0.85, label="Sancheong")
    for i, (u, s) in enumerate(zip(aucs_uiseong, aucs_sancheong)):
        ax.text(i - width/2, u + 0.005, f"{u:.3f}", ha="center", fontsize=8)
        ax.text(i + width/2, s + 0.005, f"{s:.3f}", ha="center", fontsize=8)
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.set_ylabel("ROC AUC")
    ax.set_ylim(0.3, 0.95)
    ax.set_title("Cross-site AUC: best baseline direction vs HSI v1", fontsize=12)
    ax.legend(loc="lower right")

    # ---- Row 3: lift charts ----
    for i, site in enumerate(SITES):
        ax = fig.add_subplot(gs[2, i])
        d = data[site]
        h = d["hsi"].values.astype("float32")
        if d["peri"] is None:
            continue
        burn = rasterize(((g, 1) for g in d["peri"].geometry if g is not None),
                         out_shape=h.shape,
                         transform=d["hsi"].rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h)
        burned = h[burn & valid]
        unburned = h[(~burn) & valid]
        if len(burned) == 0:
            continue
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        order = np.argsort(-s)
        deciles = np.arange(1, 11)
        lifts = [y[order[: max(1, int(len(order) * d_ / 10))]].mean() / max(y.mean(), 1e-9) for d_ in deciles]
        ax.bar(deciles, lifts, color=colors[site], alpha=0.85)
        ax.axhline(1.0, color="grey", linestyle="--")
        ax.set_xlabel("Top decile")
        ax.set_ylabel("Lift (vs random)")
        ax.set_title(f"{site.title()} — cumulative lift", fontsize=12)
        ax.set_xticks(deciles)

    fig.suptitle(
        "PineSentry-Fire v1 — pre-fire pyrophilic Hydraulic Stress Index\n"
        "EMIT (~7.4 nm SWIR) → species-aware HSI vs Korean dNBR perimeters",
        fontsize=14, y=0.995,
    )
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
