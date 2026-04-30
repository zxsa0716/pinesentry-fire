"""HSI v1.5 with SMAP root-zone soil moisture as additional feature.

Tests whether adding pre-fire 30-day SMAP root-zone soil moisture (regridded
to the HSI v1 raster) improves the AUC. Combines as:

  HSI_v1_5(i) = 0.85 × HSI_v1(i) + 0.15 × (1 - SMAP_RZSM_norm(i))

If AUC v1.5 > AUC v1, SMAP adds independent information.
If AUC v1.5 ≈ AUC v1, the radiative HSI already captures the moisture signal.

Output: data/hsi/v1_5/{site}_hsi_v1_5.tif + auc_v1_5.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr
import xarray as xr

SITES = ("uiseong", "sancheong")
OUT_DIR = Path("data/hsi/v1_5")


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}

    for site in SITES:
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        smap_npz = Path(f"data/smap_l4/pre_fire_root_sm/{site}_pre_fire_rzsm_mean.npz")
        peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not h_path.exists() or not peri_path.exists():
            print(f"{site}: missing input"); continue
        if not smap_npz.exists():
            print(f"{site}: missing SMAP {smap_npz}"); continue

        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        bnd = h.rio.bounds()  # (minx, miny, maxx, maxy)
        crs = h.rio.crs
        # Target HSI v1 grid in WGS84
        h_wgs = h.rio.reproject("EPSG:4326")
        bnd_wgs = h_wgs.rio.bounds()

        smap = np.load(smap_npz)
        sm_mean = smap["mean"]
        sm_lat = smap["lat"]
        sm_lon = smap["lon"]
        print(f"{site}: SMAP grid {sm_mean.shape}, lat {sm_lat.min():.3f}-{sm_lat.max():.3f}, "
              f"lon {sm_lon.min():.3f}-{sm_lon.max():.3f}")

        # Build a SMAP DataArray on its native grid then reproject to HSI v1 raster
        # Native SMAP grid is irregular EASE-Grid 2.0 9km; we use the per-pixel
        # lat/lon arrays as 2D coords and interpolate via scipy griddata.
        from scipy.interpolate import griddata
        finite = np.isfinite(sm_mean)
        if finite.sum() < 4:
            print(f"  no SMAP data over {site}"); continue
        pts = np.column_stack([sm_lon[finite], sm_lat[finite]])
        vals = sm_mean[finite]

        # Sample HSI v1 lat/lon
        h_lon = np.array(h_wgs.x.values)
        h_lat = np.array(h_wgs.y.values)
        LON, LAT = np.meshgrid(h_lon, h_lat)
        sm_on_h = griddata(pts, vals, (LON, LAT), method="linear")
        # Replace NaN with nearest
        nan_mask = np.isnan(sm_on_h)
        if nan_mask.any() and finite.sum() > 0:
            sm_on_h_nn = griddata(pts, vals, (LON, LAT), method="nearest")
            sm_on_h[nan_mask] = sm_on_h_nn[nan_mask]

        sm_on_h_native = xr.DataArray(sm_on_h, dims=("y", "x"),
                                      coords={"y": h_lat, "x": h_lon})
        sm_on_h_native.rio.write_crs("EPSG:4326", inplace=True)
        sm_in_crs = sm_on_h_native.rio.reproject_match(h)

        sm_arr = sm_in_crs.values
        h_arr = h.values
        sm_n = percentile_norm(sm_arr)

        h_n = h_arr  # already in [0,1]
        v15 = 0.85 * h_n + 0.15 * (1 - sm_n)
        v15 = np.where(np.isfinite(h_arr) & np.isfinite(sm_arr), v15, np.nan)

        out_tif = OUT_DIR / f"{site}_hsi_v1_5.tif"
        da_out = xr.DataArray(v15.astype("float32"), dims=("y", "x"),
                              coords={"y": h.y, "x": h.x}, name="hsi_v1_5")
        da_out.rio.write_crs(crs, inplace=True)
        da_out.rio.to_raster(out_tif, compress="LZW", tiled=True)
        print(f"  saved -> {out_tif}")

        import geopandas as gpd
        from rasterio.features import rasterize
        from sklearn.metrics import roc_auc_score
        peri = gpd.read_file(peri_path).to_crs(crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=v15.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(v15)
        burned = v15[burn & valid]
        unburned = v15[(~burn) & valid]
        if len(burned) > 5 and len(unburned) > 5:
            auc_v15 = float(roc_auc_score(
                np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))]),
                np.concatenate([burned, unburned])))
            burned_v1 = h_arr[burn & np.isfinite(h_arr)]
            unburned_v1 = h_arr[(~burn) & np.isfinite(h_arr)]
            auc_v1 = float(roc_auc_score(
                np.concatenate([np.ones(len(burned_v1)), np.zeros(len(unburned_v1))]),
                np.concatenate([burned_v1, unburned_v1])))
            burned_smap = sm_arr[burn & np.isfinite(sm_arr)]
            unburned_smap = sm_arr[(~burn) & np.isfinite(sm_arr)]
            sm_score = (1 - sm_n)
            auc_sm = float(roc_auc_score(
                np.concatenate([np.ones(len(burned_smap)), np.zeros(len(unburned_smap))]),
                np.concatenate([sm_score[burn & np.isfinite(sm_arr)],
                                sm_score[(~burn) & np.isfinite(sm_arr)]])))
            summary[site] = {
                "auc_HSI_v1": auc_v1,
                "auc_SMAP_RZSM_dryness_only": auc_sm,
                "auc_HSI_v1_5_combined": auc_v15,
                "delta_combined_minus_v1": auc_v15 - auc_v1,
            }
            print(f"  AUC v1={auc_v1:.4f}  SMAP-only={auc_sm:.4f}  v1.5={auc_v15:.4f}  delta={auc_v15-auc_v1:+.4f}")

    Path(OUT_DIR / "auc_v1_5_smap.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT_DIR / 'auc_v1_5_smap.json'}")


if __name__ == "__main__":
    main()
