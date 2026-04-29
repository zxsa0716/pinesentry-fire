"""Isotonic calibration of HSI v1 to a probability of burn.

Trains an isotonic regressor on Uiseong (large N) then tests calibration
on the other 4 sites. Useful for the v2 production-grade probability map.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT_PNG = Path("data/hsi/v1/calibration_isotonic.png")


def site_yx(site):
    h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    if not h_path.exists():
        return None
    h = rxr.open_rasterio(h_path, masked=True).squeeze()
    peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
    if not peri_path.exists():
        return None
    import geopandas as gpd
    from rasterio.features import rasterize
    peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=h.shape, transform=h.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(h.values)
    burned = h.values[burn & valid]; unburned = h.values[(~burn) & valid]
    return burned, unburned


def main():
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import brier_score_loss

    train = site_yx("uiseong")
    if train is None:
        return
    bt, ut = train
    yt = np.concatenate([np.ones(len(bt)), np.zeros(len(ut))])
    st = np.concatenate([bt, ut])
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(st, yt)
    print(f"Trained on Uiseong: {len(yt)} pixels (P_burn={yt.mean():.3f})")

    sites = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
    colors = {"uiseong": "#a50026", "sancheong": "#313695",
              "gangneung": "#1a9850", "uljin": "#984ea3", "palisades": "#fdb863"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    summary = {}

    bins = np.linspace(0, 1, 11)
    for site in sites:
        sx = site_yx(site)
        if sx is None:
            continue
        burned, unburned = sx
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s_raw = np.concatenate([burned, unburned])
        s_cal = iso.predict(s_raw)
        brier_raw = brier_score_loss(y, s_raw)
        brier_cal = brier_score_loss(y, s_cal)
        summary[site] = {"brier_raw": float(brier_raw), "brier_cal": float(brier_cal),
                         "improvement": float(brier_raw - brier_cal)}

        # Per-decile empirical fire rate (raw vs calibrated)
        for ax, sc, label in [(axes[0], s_raw, "raw"), (axes[1], s_cal, "isotonic")]:
            bin_idx = np.digitize(sc, bins) - 1
            xs, ys = [], []
            for b in range(10):
                m = bin_idx == b
                if m.sum() > 50:
                    xs.append((bins[b] + bins[b+1]) / 2)
                    ys.append(y[m].mean())
            if xs:
                ax.plot(xs, ys, "o-", color=colors[site], linewidth=2,
                        markersize=6, label=site.title())

        print(f"  {site:>10}: Brier raw={brier_raw:.4f}  cal={brier_cal:.4f}  Δ={brier_raw-brier_cal:+.4f}")

    for ax, title in [(axes[0], "Raw HSI v1"), (axes[1], "Isotonic-calibrated (trained on Uiseong)")]:
        ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1, label="Perfect calibration")
        ax.set_xlabel("Score (decile center)")
        ax.set_ylabel("Empirical fire rate")
        ax.set_title(title)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle("PineSentry-Fire v1 — Isotonic calibration cross-site\n"
                 "(monotonic mapping fitted on Uiseong, applied to all 5 sites)", y=1.01, fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=140, bbox_inches="tight")
    plt.close(fig)
    Path("data/hsi/v1/calibration_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
