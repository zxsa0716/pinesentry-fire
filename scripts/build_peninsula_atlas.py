"""8-ROI Korean peninsula HSI v1 atlas — Q7 wishlist narrative.

For each of 8 ROIs (Uiseong, Sancheong, Gangneung, Uljin, Gwangneung,
Jirisan, Seorak, Jeju):
  - Pull a clean Sentinel-2 winter scene (Dec-Mar 2024-2025)
  - Compute NDVI/NDII spectral baseline
  - Read imsangdo + DEM
  - Build HSI v1 (no perimeter eval — produces map only)
  - Save data/atlas/{roi}_hsi_v1.tif + _hero.png

Output: data/atlas/peninsula_montage.png — 4x2 panel of all ROIs.
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

PYROPHILIC = {
    "소나무": 1.0, "잣나무": 0.85, "낙엽송": 0.55, "리기다소나무": 0.95,
    "곰솔": 0.95, "잔나무": 0.7, "전나무": 0.65, "편백나무": 0.6,
    "삼나무": 0.55, "비자나무": 0.5, "은행나무": 0.3, "기타침엽수": 0.65,
    "신갈나무": 0.5, "굴참나무": 0.55, "상수리나무": 0.5, "갈참나무": 0.45,
    "졸참나무": 0.45, "기타 참나무류": 0.5, "기타참나무류": 0.5,
    "오리나무": 0.2, "자작나무": 0.25, "박달나무": 0.3, "밤나무": 0.3,
    "물푸레나무": 0.25, "서어나무": 0.25, "느티나무": 0.2, "벚나무": 0.25,
    "포플러": 0.2, "백합나무": 0.3, "아까시나무": 0.4, "고로쇠나무": 0.3,
    "기타활엽수": 0.4, "침활혼효림": 0.6, "죽림": 0.3,
    "비산림": float("nan"), "미립목지": float("nan"), "관목덤불": 0.2,
    "주거지": 0.0, "초지": 0.1, "경작지": 0.0, "수체": 0.0, "과수원": 0.0,
    "기타": 0.1, "제지": 0.0,
}
WEIGHTS = {"pyro": 0.40, "south": 0.20, "firerisk": 0.30, "pine_tx": 0.10}

ROIS = {
    "uiseong":   (128.50, 36.30, 128.90, 36.60),
    "sancheong": (127.70, 35.20, 128.00, 35.50),
    "gangneung": (128.78, 37.70, 128.95, 37.85),
    "uljin":     (129.20, 36.95, 129.60, 37.30),
    "gwangneung": (127.10, 37.70, 127.20, 37.80),
    "jirisan":   (127.60, 35.20, 127.90, 35.50),
    "seorak":    (128.30, 38.00, 128.55, 38.20),
    "jeju":      (126.50, 33.20, 126.80, 33.40),
}

OUT_DIR = Path("data/atlas")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_s2(bbox, dates="2025-01-01/2025-03-15"):
    from pystac_client import Client
    c = Client.open("https://earth-search.aws.element84.com/v1")
    items = list(c.search(
        collections=["sentinel-2-l2a"], bbox=list(bbox), datetime=dates,
        query={"eo:cloud_cover": {"lt": 25}},
    ).item_collection())
    if not items:
        return None
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100))
    return items[0]


def s2_indices(item, bbox):
    nir = rxr.open_rasterio(item.assets["nir"].href, masked=True).squeeze().rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    swir1 = rxr.open_rasterio(item.assets["swir22"].href, masked=True).squeeze().rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    red = rxr.open_rasterio(item.assets["red"].href, masked=True).squeeze().rio.clip_box(*bbox, crs="EPSG:4326", auto_expand=True)
    swir1 = swir1.rio.reproject_match(nir, resampling=Resampling.bilinear)
    red = red.rio.reproject_match(nir, resampling=Resampling.bilinear)
    eps = 1e-6
    ndvi = (nir - red) / (nir + red + eps)
    ndii = (nir - swir1) / (nir + swir1 + eps)
    return ndvi, ndii


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


def run_roi(roi, bbox):
    out_tif = OUT_DIR / f"{roi}_hsi_v1.tif"
    out_png = OUT_DIR / f"{roi}_hero.png"
    if out_tif.exists() and out_png.exists():
        print(f"  [skip] {roi}")
        return out_tif

    print(f"\n=== {roi} bbox={bbox} ===")
    item = fetch_s2(bbox)
    if item is None:
        print("  no S2 scene"); return None
    print(f"  S2: {item.id}  cc={item.properties.get('eo:cloud_cover','?')}%")

    ndvi, ndii = s2_indices(item, bbox)

    import geopandas as gpd
    from rasterio.features import rasterize
    gdf_path = Path(f"data/imsangdo/{roi}.gpkg")
    if gdf_path.exists():
        gdf = gpd.read_file(gdf_path).to_crs(ndvi.rio.crs)
        name_col = next((c for c in gdf.columns if "KOFTR" in c.upper()), "KOFTR_NM")
        gdf["_pyro"] = gdf[name_col].astype(str).str.strip().map(PYROPHILIC).fillna(0.30)
        pyro = rasterize(
            ((g, v) for g, v in zip(gdf.geometry, gdf["_pyro"]) if g and not np.isnan(v)),
            out_shape=ndvi.shape, transform=ndvi.rio.transform(), fill=0.30, dtype="float32",
        )
    else:
        pyro = np.full(ndvi.shape, 0.30, dtype="float32")

    dem_path = Path(f"data/dem/copdem30_{roi}.tif")
    if dem_path.exists():
        dem = rxr.open_rasterio(dem_path, masked=True).squeeze().rio.reproject_match(ndvi)
        res = abs(float(ndvi.y[1] - ndvi.y[0])) * 111000
        aspect = slope_aspect(dem.values, res)
        south = (np.cos(np.deg2rad(aspect - 180)) + 1) / 2
    else:
        south = np.zeros(ndvi.shape, dtype="float32")

    firerisk_s2 = 1.0 - ndii.values
    pyro_n = percentile_norm(pyro)
    south_n = percentile_norm(south)
    fr_n = percentile_norm(firerisk_s2)
    tx_n = percentile_norm(pyro * south)

    hsi_v1 = (
        WEIGHTS["pyro"] * pyro_n + WEIGHTS["south"] * south_n
        + WEIGHTS["firerisk"] * fr_n + WEIGHTS["pine_tx"] * tx_n
    )
    da = xr.DataArray(hsi_v1.astype("float32"), dims=("y", "x"),
                      coords={"y": ndvi.y, "x": ndvi.x}, name="hsi_v1_atlas")
    da.rio.write_crs(ndvi.rio.crs, inplace=True)
    da.rio.to_raster(out_tif, compress="LZW", tiled=True)

    # Quick PNG (always in EPSG:4326 lat/lon for legibility)
    da_wgs = da.rio.reproject("EPSG:4326")
    fig, ax = plt.subplots(figsize=(7, 6))
    extent = list(da_wgs.rio.bounds())
    im = ax.imshow(da_wgs.values, origin="upper", cmap="YlOrRd", vmin=0, vmax=1,
                   extent=[extent[0], extent[2], extent[1], extent[3]])
    plt.colorbar(im, ax=ax, label="HSI v1")
    ax.set_title(f"{roi.title()} — HSI v1 (S2 winter pre-fire)")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    fig.savefig(out_png, dpi=120, bbox_inches="tight"); plt.close(fig)

    print(f"  saved {out_tif} + {out_png}")
    return out_tif


def make_montage():
    """4x2 montage of all 8 ROI HSI maps."""
    fig, axes = plt.subplots(2, 4, figsize=(22, 11))
    for ax, roi in zip(axes.ravel(), ROIS.keys()):
        p = OUT_DIR / f"{roi}_hsi_v1.tif"
        if not p.exists():
            ax.set_visible(False); continue
        try:
            da = rxr.open_rasterio(p, masked=True).squeeze().rio.reproject("EPSG:4326")
        except Exception:
            ax.set_visible(False); continue
        extent = list(da.rio.bounds())
        im = ax.imshow(da.values, origin="upper", cmap="YlOrRd", vmin=0, vmax=1,
                       extent=[extent[0], extent[2], extent[1], extent[3]])
        ax.set_title(f"{roi.title()}", fontsize=11)
        ax.set_xlabel("lon"); ax.set_ylabel("lat")
    fig.suptitle("PineSentry-Fire v1 — Korean peninsula atlas (8 ROIs, Sentinel-2 winter pre-fire)",
                 fontsize=14, y=0.995)
    fig.tight_layout()
    out = OUT_DIR / "peninsula_montage.png"
    fig.savefig(out, dpi=120, bbox_inches="tight"); plt.close(fig)
    print(f"\nsaved montage -> {out}")


def main():
    for roi, bbox in ROIS.items():
        try:
            run_roi(roi, bbox)
        except Exception as e:
            print(f"  FAIL [{roi}]: {e}", file=sys.stderr)
    make_montage()


if __name__ == "__main__":
    main()
