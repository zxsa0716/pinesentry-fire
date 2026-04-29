"""US cross-continent v1 validation — Palisades 2025 fire (LA, January 7).

Uses the NIFC WFIGS Palisades perimeter + Tanager Open Data scenes +
COP-DEM 30m + ESA WorldCover 10m. Korean imsangdo isn't available for
US so the pyrophilic factor is approximated from WorldCover class
(Tree=0.6, Shrub=0.5, etc.) — v1-Lite for cross-continent generalization.

If AUC > 0.6 with weights identical to Korean Uiseong, it confirms the
HSI framework generalizes beyond the Korean species table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr
import xarray as xr
from rasterio.enums import Resampling

OUT = Path("data/hsi/v1/palisades_v1.tif")
OUT_PNG = Path("data/hsi/v1/palisades_v1_eval.png")
PALISADES_BBOX = (-118.60, 34.00, -118.45, 34.15)

# Pyrophilic by WorldCover class
WC_PYRO = {
    10: 0.65,  # Tree cover (assume mostly shrub-pine in SoCal)
    20: 0.50,  # Shrubland (chaparral, very fire-prone)
    30: 0.30,  # Grassland
    40: 0.10,  # Cropland
    50: 0.05,  # Built-up
    60: 0.10,  # Bare / sparse
    70: 0.0,   # Snow
    80: 0.0,   # Water
    90: 0.10,  # Wetland
    95: 0.0,   # Mangrove
    100: 0.20, # Moss / lichen
    0:   0.30, # default
}
WEIGHTS = {"pyro": 0.40, "south": 0.20, "firerisk": 0.30, "pine_tx": 0.10}


def fetch_s2_pre_palisades():
    """S2 pre-fire window — December 2024."""
    from pystac_client import Client
    c = Client.open("https://earth-search.aws.element84.com/v1")
    items = list(c.search(
        collections=["sentinel-2-l2a"],
        bbox=list(PALISADES_BBOX),
        datetime="2024-12-01/2025-01-06",
        query={"eo:cloud_cover": {"lt": 20}},
    ).item_collection())
    if not items:
        return None
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100))
    return items[0]


def s2_indices(item, bbox):
    nir = rxr.open_rasterio(item.assets["nir"].href, masked=True).squeeze().rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    swir1 = rxr.open_rasterio(item.assets["swir22"].href, masked=True).squeeze().rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    swir1 = swir1.rio.reproject_match(nir, resampling=Resampling.bilinear)
    eps = 1e-6
    ndii = (nir - swir1) / (nir + swir1 + eps)
    return nir, ndii


def slope_aspect(dem, res):
    dz_dx = np.zeros_like(dem); dz_dy = np.zeros_like(dem)
    dz_dx[:, 1:-1] = (dem[:, 2:] - dem[:, :-2]) / (2 * res)
    dz_dy[1:-1, :] = (dem[:-2, :] - dem[2:, :]) / (2 * res)
    aspect_rad = np.arctan2(dz_dy, -dz_dx)
    return (90 - np.degrees(aspect_rad)) % 360


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def main():
    item = fetch_s2_pre_palisades()
    if item is None:
        print("no S2 scene in window"); return
    print(f"S2: {item.id}  cc={item.properties.get('eo:cloud_cover')}%")
    nir, ndii = s2_indices(item, PALISADES_BBOX)

    # WorldCover -> pyrophilic
    wc_path = Path("data/worldcover/worldcover_palisades.tif")
    if wc_path.exists():
        wc = rxr.open_rasterio(wc_path, masked=False).squeeze()
        wc_match = wc.rio.reproject_match(nir, resampling=Resampling.nearest)
        pyro = np.vectorize(WC_PYRO.get)(wc_match.values, 0.30).astype("float32")
    else:
        pyro = np.full(nir.shape, 0.30, dtype="float32")

    # DEM -> south_facing
    dem_path = Path("data/dem/copdem30_palisades.tif")
    if dem_path.exists():
        dem = rxr.open_rasterio(dem_path, masked=True).squeeze().rio.reproject_match(nir)
        res = abs(float(nir.y[1] - nir.y[0])) * 111000
        aspect = slope_aspect(dem.values, res)
        south = (np.cos(np.deg2rad(aspect - 180)) + 1) / 2
    else:
        south = np.zeros(nir.shape, dtype="float32")

    firerisk = 1.0 - ndii.values
    pyro_n = percentile_norm(pyro)
    south_n = percentile_norm(south)
    fr_n = percentile_norm(firerisk)
    tx_n = percentile_norm(pyro * south)
    hsi = (WEIGHTS["pyro"] * pyro_n + WEIGHTS["south"] * south_n
           + WEIGHTS["firerisk"] * fr_n + WEIGHTS["pine_tx"] * tx_n)

    da = xr.DataArray(hsi.astype("float32"), dims=("y", "x"),
                      coords={"y": nir.y, "x": nir.x}, name="hsi_v1_palisades")
    da.rio.write_crs(nir.rio.crs, inplace=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    da.rio.to_raster(OUT, compress="LZW", tiled=True)
    print(f"saved -> {OUT}")

    # Evaluate against NIFC perimeter
    nifc = Path("data/fire_perimeter/nifc_palisades_2025.geojson")
    if not nifc.exists():
        print("  no NIFC perimeter"); return
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve
    peri = gpd.read_file(nifc).to_crs(nir.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=hsi.shape, transform=nir.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(hsi)
    burned = hsi[burn & valid]; unburned = hsi[(~burn) & valid]
    print(f"burned: n={len(burned)}, mean={np.mean(burned):.3f}")
    print(f"unburned: n={len(unburned)}, mean={np.mean(unburned):.3f}")
    if len(burned) < 10:
        print("too few burn pixels in S2 grid"); return
    y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
    s = np.concatenate([burned, unburned])
    auc = roc_auc_score(y, s)
    fpr, tpr, _ = roc_curve(y, s)
    order = np.argsort(-s)
    top10 = order[: max(1, len(order) // 10)]
    lift = (y[top10].mean()) / max(y.mean(), 1e-9)
    print(f"\nUS Palisades 2025-01 — HSI v1 (Korean weights, US WorldCover pyrophilic):")
    print(f"  AUC = {auc:.4f}, lift@10% = {lift:.2f}x, n_burn = {len(burned)}")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    bins = np.linspace(0, 1, 41)
    axes[0].hist(unburned, bins=bins, density=True, alpha=0.55, color="#1a9850", label=f"unburned (n={len(unburned):,})")
    axes[0].hist(burned, bins=bins, density=True, alpha=0.7, color="#a50026", label=f"burned (n={len(burned):,})")
    axes[0].set_xlabel("HSI v1"); axes[0].set_ylabel("Density")
    axes[0].set_title("Pre-fire HSI distribution"); axes[0].legend()

    axes[1].plot(fpr, tpr, color="#a50026", linewidth=2)
    axes[1].plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    axes[1].set_xlabel("FPR"); axes[1].set_ylabel("TPR")
    axes[1].set_title(f"ROC (AUC = {auc:.3f})  vs Korean Uiseong (0.747)")
    axes[1].set_xlim(0, 1); axes[1].set_ylim(0, 1)

    fig.suptitle(f"PineSentry-Fire v1 — US Palisades 2025-01 cross-continent test\n"
                 f"Korean weights + US WorldCover pyrophilic | n_burn={len(burned)} | lift@10%={lift:.2f}x", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=140, bbox_inches="tight"); plt.close(fig)
    print(f"saved -> {OUT_PNG}")


if __name__ == "__main__":
    main()
