"""Animated GIF cycling through 5-site ROC curves with growing AUC bar.

Output: examples/figures/17_animated_5site_roc.gif
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr

OUT = Path("examples/figures/17_animated_5site_roc.gif")

SITES = [
    ("uiseong",   "data/hsi/v1/uiseong_hsi_v1.tif",   "data/fire_perimeter/synth_uiseong_dnbr.gpkg",   "EMIT 285b · 의성 2025-03",   "#a50026"),
    ("sancheong", "data/hsi/v1/sancheong_hsi_v1.tif", "data/fire_perimeter/synth_sancheong_dnbr.gpkg", "EMIT 285b · 산청 2025-03",   "#d73027"),
    ("gangneung", "data/hsi/v1/gangneung_hsi_v1.tif", "data/fire_perimeter/synth_gangneung_dnbr.gpkg", "S2 13b · 강릉 2023-04",     "#fc8d59"),
    ("uljin",     "data/hsi/v1/uljin_hsi_v1.tif",     "data/fire_perimeter/synth_uljin_dnbr.gpkg",     "S2 13b · 울진 2022-03",     "#fdae61"),
    ("palisades", "data/hsi/v1/palisades_hsi_v1.tif", "data/fire_perimeter/nifc_palisades_2025.geojson","S2 13b · LA Palisades 2025-01 (US)", "#984ea3"),
]


def main():
    import imageio.v3 as iio
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve

    rng = np.random.default_rng(0)

    # Pre-compute (fpr, tpr, auc) for each site
    site_data = []
    for site, h_path, peri_path, label, col in SITES:
        if not (Path(h_path).exists() and Path(peri_path).exists()):
            continue
        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values)
        burned = h.values[burn & valid]; unburned = h.values[(~burn) & valid]
        if len(burned) < 5: continue
        n_b = min(5000, len(burned)); n_u = min(50000, len(unburned))
        bi = rng.choice(len(burned), n_b, replace=False)
        ui = rng.choice(len(unburned), n_u, replace=False)
        y = np.concatenate([np.ones(n_b), np.zeros(n_u)])
        s = np.concatenate([burned[bi], unburned[ui]])
        fpr, tpr, _ = roc_curve(y, s)
        auc = float(roc_auc_score(y, s))
        site_data.append({"site": site, "label": label, "col": col,
                           "fpr": fpr, "tpr": tpr, "auc": auc})
        print(f"  {site}: AUC = {auc:.3f}")

    # Build frames: each frame highlights one site's ROC + accumulates earlier ones
    frames = []
    for k in range(1, len(site_data) + 1):
        fig, (ax, axb) = plt.subplots(1, 2, figsize=(11, 5),
                                        gridspec_kw={"width_ratios": [3, 2]})
        for i, d in enumerate(site_data[:k]):
            alpha = 1.0 if i == k - 1 else 0.45
            lw = 3.0 if i == k - 1 else 1.6
            ax.plot(d["fpr"], d["tpr"], color=d["col"], linewidth=lw, alpha=alpha,
                    label=f"{d['label']}  AUC={d['auc']:.3f}")
        ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=0.8)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
        ax.set_title(f"Site {k} of {len(site_data)} — pre-registered HSI v1 (identical weights)",
                     fontsize=12)
        ax.legend(loc="lower right", fontsize=9)

        # Bar chart accumulating
        names = [d["site"].title() for d in site_data[:k]]
        aucs_seen = [d["auc"] for d in site_data[:k]]
        cols_seen = [d["col"] for d in site_data[:k]]
        bars = axb.barh(names, aucs_seen, color=cols_seen)
        for bar, a in zip(bars, aucs_seen):
            axb.text(a + 0.005, bar.get_y() + bar.get_height()/2, f"{a:.3f}",
                     va="center", fontsize=9)
        axb.set_xlim(0.5, 0.85); axb.axvline(0.5, color="grey", linestyle="--", linewidth=0.6)
        axb.set_xlabel("ROC AUC")
        axb.set_title("AUC accumulator", fontsize=12)
        axb.invert_yaxis()

        fig.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        plt.close(fig)
        buf.seek(0)
        from PIL import Image
        frames.append(np.array(Image.open(buf).convert("RGB")))

    # Pad final frame for emphasis (extra repetition)
    frames_extended = frames + [frames[-1]] * 3

    # Pad to common shape
    max_h = max(f.shape[0] for f in frames_extended)
    max_w = max(f.shape[1] for f in frames_extended)
    padded = []
    for f in frames_extended:
        h, w, _ = f.shape
        pad = np.full((max_h, max_w, 3), 255, dtype=np.uint8)
        pad[:h, :w] = f
        padded.append(pad)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(OUT, padded, duration=1200, loop=0, plugin="pillow")
    print(f"\nsaved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
