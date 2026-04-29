"""Grand Hero figure for the August submission — 9-panel layout.

Layout:
  Row 1: Uiseong HSI v1 + dNBR  |  Sancheong HSI v1 + dNBR  |  ROC overlay (4 sites)
  Row 2: AUC bar (HSI v1 vs NDVI/NDMI/NDII × 4 sites)  |  Lift Uiseong  |  Lift Sancheong
  Row 3: Peninsula atlas montage spanning the full row (8 sub-ROIs)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT = Path("data/hsi/v1/HERO_GRAND.png")
SITES_EMIT = ("uiseong", "sancheong")
SITES_S2 = ("gangneung", "uljin")
ATLAS_ROIS = ["uiseong", "sancheong", "gangneung", "uljin", "gwangneung", "jirisan", "seorak", "jeju"]


def load_v1(site: str):
    p = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    if p.exists():
        return rxr.open_rasterio(p, masked=True).squeeze()
    return None


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(20, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.40, wspace=0.30)

    cmap = "YlOrRd"

    # Row 1 col 1-2: HSI v1 maps + perimeters for Uiseong + Sancheong
    for i, site in enumerate(SITES_EMIT):
        ax = fig.add_subplot(gs[0, i])
        h = load_v1(site)
        if h is None:
            ax.set_visible(False); continue
        bounds = list(h.rio.bounds())
        im = ax.imshow(h.values, origin="upper", cmap=cmap, vmin=0, vmax=1,
                       extent=[bounds[0], bounds[2], bounds[1], bounds[3]])
        try:
            import geopandas as gpd
            peri = gpd.read_file(f"data/fire_perimeter/synth_{site}_dnbr.gpkg").to_crs(h.rio.crs)
            peri.plot(ax=ax, facecolor="black", alpha=0.20, edgecolor="black", linewidth=1.2)
        except Exception:
            pass
        ax.set_title(f"{site.title()} — HSI v1 + dNBR perimeter", fontsize=12)
        ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="HSI v1")

    # Row 1 col 3: ROC overlay
    ax = fig.add_subplot(gs[0, 2])
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve
    colors = {"uiseong": "#a50026", "sancheong": "#313695", "gangneung": "#1a9850", "uljin": "#984ea3"}
    aucs = {}
    for site in list(SITES_EMIT) + list(SITES_S2):
        h = load_v1(site)
        if h is None:
            print(f"  {site}: no v1 tif")
            continue
        try:
            import geopandas as gpd
            peri = gpd.read_file(f"data/fire_perimeter/synth_{site}_dnbr.gpkg").to_crs(h.rio.crs)
        except Exception as e:
            print(f"  {site}: peri load fail {e}")
            continue
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(), fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]
        unburned = h.values[(~burn) & valid]
        print(f"  {site}: burned={len(burned)}, unburned={len(unburned)}")
        if len(burned) < 5:
            continue
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        try:
            auc = roc_auc_score(y, s)
        except Exception:
            continue
        aucs[site] = auc
        fpr, tpr, _ = roc_curve(y, s)
        sensor = "EMIT 285" if site in SITES_EMIT else "S2 13"
        ax.plot(fpr, tpr, color=colors[site], linewidth=2,
                label=f"{site.title()} ({sensor}b)  AUC={auc:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("v1 ROC — 4 Korean fire sites, identical weights", fontsize=12)
    ax.legend(loc="lower right", fontsize=9)

    # Row 2 col 1: AUC bar chart vs baselines (Uiseong + Sancheong only — others have no baseline file)
    ax = fig.add_subplot(gs[1, 0])
    methods = ["NDVI", "NDMI", "NDII", "HSI_v1"]
    method_colors = {"NDVI": "#fc8d59", "NDMI": "#74add1", "NDII": "#984ea3", "HSI_v1": "#a50026"}
    width = 0.35
    x = np.arange(len(methods))
    aucs_uiseong = []
    aucs_sancheong = []
    try:
        u_summary = json.loads(Path("data/baselines/uiseong_summary.json").read_text())
        s_summary = json.loads(Path("data/baselines/sancheong_summary.json").read_text())
        aucs_uiseong = [u_summary[m]["auc"] for m in methods]
        aucs_sancheong = [s_summary[m]["auc"] for m in methods]
        ax.bar(x - width/2, aucs_uiseong, width, color="#fc8d59", alpha=0.85, label="Uiseong")
        ax.bar(x + width/2, aucs_sancheong, width, color="#313695", alpha=0.85, label="Sancheong")
        for i, (u, s) in enumerate(zip(aucs_uiseong, aucs_sancheong)):
            ax.text(i - width/2, u + 0.005, f"{u:.3f}", ha="center", fontsize=8)
            ax.text(i + width/2, s + 0.005, f"{s:.3f}", ha="center", fontsize=8)
    except Exception as e:
        ax.text(0.5, 0.5, f"baselines summary missing\n{e}", ha="center", transform=ax.transAxes)
    ax.axhline(0.5, color="grey", linestyle="--")
    ax.set_xticks(x); ax.set_xticklabels(methods)
    ax.set_ylabel("ROC AUC"); ax.set_ylim(0.3, 0.95)
    ax.set_title("v1 vs spectral baselines (best direction per index)", fontsize=12)
    ax.legend(loc="lower right")

    # Row 2 col 2-3: Lift charts for Uiseong + Sancheong
    for i, site in enumerate(SITES_EMIT):
        ax = fig.add_subplot(gs[1, i + 1])
        h = load_v1(site)
        if h is None:
            ax.set_visible(False); continue
        try:
            import geopandas as gpd
            peri = gpd.read_file(f"data/fire_perimeter/synth_{site}_dnbr.gpkg").to_crs(h.rio.crs)
        except Exception:
            ax.set_visible(False); continue
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(), fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]; unburned = h.values[(~burn) & valid]
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        order = np.argsort(-s)
        deciles = np.arange(1, 11)
        lifts = [y[order[: max(1, int(len(order) * d / 10))]].mean() / max(y.mean(), 1e-9) for d in deciles]
        ax.bar(deciles, lifts, color=colors[site], alpha=0.85)
        ax.axhline(1.0, color="grey", linestyle="--")
        ax.set_xlabel("Top decile"); ax.set_ylabel("Lift")
        ax.set_title(f"{site.title()} — cumulative lift", fontsize=12)
        ax.set_xticks(deciles)

    # Row 3: Peninsula 8-ROI atlas
    sub_gs = gs[2, :].subgridspec(2, 4, hspace=0.30, wspace=0.10)
    for k, roi in enumerate(ATLAS_ROIS):
        ax = fig.add_subplot(sub_gs[k // 4, k % 4])
        p = Path(f"data/atlas/{roi}_hsi_v1.tif")
        if not p.exists():
            ax.set_visible(False); continue
        try:
            da = rxr.open_rasterio(p, masked=True).squeeze().rio.reproject("EPSG:4326")
        except Exception:
            ax.set_visible(False); continue
        bounds = list(da.rio.bounds())
        ax.imshow(da.values, origin="upper", cmap="YlOrRd", vmin=0, vmax=1,
                  extent=[bounds[0], bounds[2], bounds[1], bounds[3]])
        ax.set_title(roi.title(), fontsize=10)
        ax.set_xlabel("lon", fontsize=8); ax.set_ylabel("lat", fontsize=8)
        ax.tick_params(labelsize=7)

    fig.suptitle(
        "PineSentry-Fire v1 — pre-fire pyrophilic Hydraulic Stress Index\n"
        "EMIT (~7.4 nm SWIR) + Korean Forest Service imsangdo + COP-DEM 30m → species-aware HSI\n"
        "Validated against 4 Korean dNBR perimeters (Uiseong 2025, Sancheong 2025, Gangneung 2023, Uljin 2022)\n"
        "with identical weights, plus 8-ROI peninsula atlas (Q7 wishlist coverage)",
        fontsize=13, y=0.995,
    )
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
