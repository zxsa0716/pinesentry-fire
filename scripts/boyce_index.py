"""Continuous Boyce index for presence-only fire prediction validation.

Boyce 2002: bin the score range, compute (presences in bin / available in bin),
expected ratio is 1 under null (random). Compute Spearman correlation
between bin centers and the observed/expected ratio. Boyce index ranges
[-1, 1]: 1 = perfect predictor, 0 = random, -1 = anti-predictor.

Useful when burn is rare and we don't fully trust the unburned class
definition (some "unburned" pixels may have been burned in past years).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr
from scipy.stats import spearmanr

SITES = ("uiseong", "sancheong", "gangneung", "uljin", "palisades")
N_BINS = 10


def boyce_continuous(score, presence, n_bins=10, window=0.1):
    """Continuous Boyce index — sliding window over score range."""
    score = np.asarray(score, dtype="float64")
    presence = np.asarray(presence, dtype=bool)
    pres_score = score[presence]
    if len(pres_score) < 5:
        return None, None, None

    centers = np.linspace(0, 1, n_bins + 1)[:-1] + 1.0/(2*n_bins)
    half = window / 2
    pred_e = []
    boyce_pe = []
    for c in centers:
        in_window = (score >= c - half) & (score < c + half)
        if in_window.sum() < 10:
            continue
        p = ((presence & in_window).sum()) / max(in_window.sum(), 1)
        e = presence.mean()
        ratio = p / max(e, 1e-9)
        pred_e.append(c); boyce_pe.append(ratio)

    if len(boyce_pe) < 3:
        return None, None, None
    rho, _ = spearmanr(pred_e, boyce_pe)
    return float(rho), pred_e, boyce_pe


def main():
    import geopandas as gpd
    from rasterio.features import rasterize

    summary = {}
    fig, axes = plt.subplots(1, len(SITES), figsize=(20, 4))

    for ax, site in zip(axes.ravel(), SITES):
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        if not h_path.exists():
            ax.set_visible(False); continue
        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri_path = Path("data/fire_perimeter/nifc_palisades_2025.geojson") if site == "palisades" \
                    else Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not peri_path.exists():
            ax.set_visible(False); continue
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        score = h.values[valid]
        presence = burn[valid]
        if presence.sum() < 10:
            ax.set_visible(False); continue

        rho, centers, ratios = boyce_continuous(score, presence)
        summary[site] = {"boyce_rho": rho, "n_bins": len(ratios) if ratios else 0,
                         "n_presence": int(presence.sum())}
        print(f"  {site:>10}: Boyce rho = {rho:.3f}  (n_pres={presence.sum()})")

        if centers and ratios:
            ax.plot(centers, ratios, "o-", color="#a50026", linewidth=2)
            ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.7)
            ax.set_title(f"{site.title()}  rho={rho:.3f}", fontsize=10)
            ax.set_xlabel("HSI v1 score"); ax.set_ylabel("P(presence)/E(presence)")
            ax.set_xlim(0, 1)

    fig.suptitle("PineSentry-Fire v1 — continuous Boyce index (sliding window 0.1)", fontsize=12, y=1.02)
    fig.tight_layout()
    out = Path("data/hsi/v1/boyce_index.png")
    fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close(fig)
    Path("data/hsi/v1/boyce_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
