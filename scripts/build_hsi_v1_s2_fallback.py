"""HSI v1 for sites without EMIT pre-fire coverage (Gangneung 2023, Uljin 2022).

Replaces EMIT-derived empirical FireRisk_v0 with Sentinel-2 NDMI/NDII
computed from a single pre-fire scene matching dNBR pre-fire window.
The species pyrophilic factor + south-facing slope come from the same
sources as the EMIT v1 pipeline.
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

SITES = {
    "gangneung": {"bbox": [128.78, 37.70, 128.95, 37.85], "fire_date": "2023-04-11"},
    "uljin":     {"bbox": [129.20, 36.95, 129.60, 37.30], "fire_date": "2022-03-04"},
}


def fetch_s2_pre_fire(site: str, info):
    """Pull the cleanest Sentinel-2 scene 30-60 days before the fire."""
    from datetime import date, timedelta
    from pystac_client import Client
    fire_dt = date.fromisoformat(info["fire_date"])
    start = (fire_dt - timedelta(days=90)).isoformat()
    end = (fire_dt - timedelta(days=1)).isoformat()
    c = Client.open("https://earth-search.aws.element84.com/v1")
    items = list(c.search(
        collections=["sentinel-2-l2a"],
        bbox=info["bbox"],
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": 30}},
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


def percentile_norm(arr):
    m = np.isfinite(arr)
    if m.sum() < 10:
        return np.zeros_like(arr)
    plo, phi = np.nanpercentile(arr[m], [5, 95])
    if phi <= plo:
        return np.zeros_like(arr)
    return np.clip((arr - plo) / (phi - plo), 0, 1)


def slope_aspect(dem, res):
    dz_dx = np.zeros_like(dem); dz_dy = np.zeros_like(dem)
    dz_dx[:, 1:-1] = (dem[:, 2:] - dem[:, :-2]) / (2 * res)
    dz_dy[1:-1, :] = (dem[:-2, :] - dem[2:, :]) / (2 * res)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect_rad = np.arctan2(dz_dy, -dz_dx)
    aspect_deg = (90 - np.degrees(aspect_rad)) % 360
    return np.degrees(slope_rad).astype("float32"), aspect_deg.astype("float32")


def run_site(site, info):
    print(f"\n=== {site} ({info['fire_date']}) ===")
    item = fetch_s2_pre_fire(site, info)
    if item is None:
        print("  no S2 pre-fire scene"); return None
    print(f"  S2 scene: {item.id}  cc={item.properties.get('eo:cloud_cover', '?')}%")

    ndvi, ndii = s2_indices(item, info["bbox"])
    grid = ndvi  # use S2 NIR grid as reference

    # Load imsangdo polygons + rasterize pyrophilic
    import geopandas as gpd
    from rasterio.features import rasterize
    gdf_path = Path(f"data/imsangdo/{site}.gpkg")
    if not gdf_path.exists():
        print(f"  imsangdo missing: {gdf_path}"); return None
    gdf = gpd.read_file(gdf_path).to_crs(ndvi.rio.crs)
    name_col = next((c for c in gdf.columns if "KOFTR" in c.upper()), "KOFTR_NM")
    gdf["_pyro"] = gdf[name_col].astype(str).str.strip().map(PYROPHILIC).fillna(0.30)

    pyro = rasterize(
        ((g, v) for g, v in zip(gdf.geometry, gdf["_pyro"]) if g and not np.isnan(v)),
        out_shape=ndvi.shape, transform=ndvi.rio.transform(), fill=0.30, dtype="float32",
    )

    # DEM
    dem_path = Path(f"data/dem/copdem30_{site}.tif")
    if dem_path.exists():
        dem = rxr.open_rasterio(dem_path, masked=True).squeeze()
        dem_match = dem.rio.reproject_match(ndvi)
        lat0 = float(ndvi.y.mean())
        res = abs(float(ndvi.y[1] - ndvi.y[0])) * 111000
        slope, aspect = slope_aspect(dem_match.values, res)
        south = (np.cos(np.deg2rad(aspect - 180)) + 1) / 2
    else:
        south = np.zeros(ndvi.shape, dtype="float32")
        print("  DEM missing — south_facing = 0")

    # FireRisk_S2 = 1 - NDII (S2 fallback for EMIT-derived firerisk)
    firerisk_s2 = 1.0 - ndii.values

    pyro_n = percentile_norm(pyro)
    south_n = percentile_norm(south)
    fr_n = percentile_norm(firerisk_s2)
    tx_n = percentile_norm(pyro * south)

    hsi_v1 = (
        WEIGHTS["pyro"] * pyro_n + WEIGHTS["south"] * south_n
        + WEIGHTS["firerisk"] * fr_n + WEIGHTS["pine_tx"] * tx_n
    )

    out = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    da = xr.DataArray(hsi_v1.astype("float32"), dims=("y", "x"), coords={"y": ndvi.y, "x": ndvi.x}, name="hsi_v1_s2")
    da.rio.write_crs(ndvi.rio.crs, inplace=True)   # match S2 native UTM
    da.rio.to_raster(out, compress="LZW", tiled=True)

    # Evaluate
    peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
    if not peri_path.exists():
        print(f"  no perimeter; skip eval"); return None
    peri = gpd.read_file(peri_path).to_crs(ndvi.rio.crs)   # match NDVI's UTM CRS
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=hsi_v1.shape, transform=ndvi.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(hsi_v1)
    burned = hsi_v1[burn & valid]
    unburned = hsi_v1[(~burn) & valid]
    print(f"  burned: n={len(burned)}, mean={np.mean(burned):.3f}")
    print(f"  unburned: n={len(unburned)}, mean={np.mean(unburned):.3f}")
    if len(burned) > 5 and len(unburned) > 5:
        from sklearn.metrics import roc_auc_score
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        auc = roc_auc_score(y, s)
        order = np.argsort(-s)
        top10 = order[: max(1, len(order) // 10)]
        lift = (y[top10].mean()) / max(y.mean(), 1e-9)
        print(f"  HSI v1 (S2 fallback) AUC = {auc:.4f}  lift = {lift:.2f}x")
        return {"site": site, "auc": auc, "lift": lift, "n_burn": int(len(burned)), "n_unburn": int(len(unburned))}


def main():
    results = {}
    for site, info in SITES.items():
        r = run_site(site, info)
        if r:
            results[site] = r
    print(f"\n=== Summary ===")
    for s, r in results.items():
        print(f"  {s}: AUC={r['auc']:.3f}  lift={r['lift']:.2f}x  n_burn={r['n_burn']}")


if __name__ == "__main__":
    main()
