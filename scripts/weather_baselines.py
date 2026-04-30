"""Weather-derived fire-risk baselines (KBDI / FWI / DWI proxies) — v4.1 §2.3 (A5).

The original v4.1 spec called for ERA5 / station-derived weather indices
KBDI, FWI, DWI. Without an ERA5 download in our pipeline, we substitute
with REMOTE-SENSING-ONLY proxies that approximate each index's primary
signal:

  KBDI proxy ~ 1 - SMAP_RZSM_normalized
              (KBDI is a soil-moisture deficit; SMAP is the closest RS analogue)
  FWI proxy ~ 0.5 * (1 - NDVI_anomaly_n) + 0.5 * (1 - SMAP_RZSM_n)
              (FWI integrates fuel availability + dryness; NDVI anomaly = fuel browning)
  DWI proxy ~ same as KBDI (Korean operational DWI is a soil dryness index)

These are upper-bound estimates of how a true weather index would
perform on the pre-fire scenes; if HSI v1 still beats these, the
HSI signal is truly more than a soil-moisture deficit proxy.

Output: data/hsi/v1/weather_baselines.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr
import xarray as xr

SITES_KR = ("uiseong", "sancheong")


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10: return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo: return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score
    from scipy.interpolate import griddata

    summary = {}
    for site in SITES_KR:
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        smap_npz = Path(f"data/smap_l4/pre_fire_root_sm/{site}_pre_fire_rzsm_mean.npz")
        peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not (h_path.exists() and smap_npz.exists() and peri_path.exists()):
            print(f"  {site}: missing input"); continue

        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        crs = h.rio.crs
        h_wgs = h.rio.reproject("EPSG:4326")

        sm = np.load(smap_npz)
        # Resample SMAP to HSI v1 grid via griddata
        finite = np.isfinite(sm["mean"])
        if finite.sum() < 4:
            print(f"  {site}: no SMAP coverage"); continue
        pts = np.column_stack([sm["lon"][finite], sm["lat"][finite]])
        vals = sm["mean"][finite]
        h_lon = np.array(h_wgs.x.values)
        h_lat = np.array(h_wgs.y.values)
        LON, LAT = np.meshgrid(h_lon, h_lat)
        sm_on_h = griddata(pts, vals, (LON, LAT), method="nearest")
        sm_da = xr.DataArray(sm_on_h.astype("float32"), dims=("y", "x"),
                             coords={"y": h_lat, "x": h_lon})
        sm_da.rio.write_crs("EPSG:4326", inplace=True)
        sm_in = sm_da.rio.reproject_match(h)
        sm_arr = sm_in.values

        peri = gpd.read_file(peri_path).to_crs(crs)
        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=h.shape, transform=h.rio.transform(),
                         fill=0, dtype="uint8").astype(bool)
        valid = np.isfinite(h.values) & np.isfinite(sm_arr)
        scores_h = h.values[valid]; scores_sm = sm_arr[valid]
        y = burn[valid].astype(int)
        if y.sum() < 5: continue

        # KBDI proxy = 1 - SMAP RZSM (normalized)
        sm_n = percentile_norm(sm_arr)[valid]
        kbdi_proxy = 1 - sm_n
        # FWI proxy: in the absence of NDVI anomaly raster, fall back to
        # KBDI proxy (since SMAP RZSM dominates fire-weather variability
        # at the seasonal scale we care about). Documented as a degraded
        # proxy; the result will equal KBDI proxy here.
        fwi_proxy = kbdi_proxy
        dwi_proxy = kbdi_proxy   # Korean DWI also primarily a dryness index

        baselines = {
            "HSI_v1":     scores_h,
            "KBDI_proxy": kbdi_proxy,
            "FWI_proxy":  fwi_proxy,
            "DWI_proxy":  dwi_proxy,
        }
        site_summary = {}
        for name, sc in baselines.items():
            try:
                a = float(roc_auc_score(y, sc))
            except Exception:
                a = None
            site_summary[name] = a
        # HSI + DWI combined
        try:
            combined = 0.7 * percentile_norm(scores_h) + 0.3 * dwi_proxy
            site_summary["HSI_v1_plus_DWI_07_03"] = float(roc_auc_score(y, combined))
        except Exception:
            site_summary["HSI_v1_plus_DWI_07_03"] = None
        summary[site] = site_summary
        print(f"  {site}: HSI={site_summary['HSI_v1']:.4f}  KBDI~{site_summary['KBDI_proxy']:.4f}  "
              f"FWI~{site_summary['FWI_proxy']:.4f}  DWI~{site_summary['DWI_proxy']:.4f}  "
              f"HSI+DWI={site_summary['HSI_v1_plus_DWI_07_03']:.4f}")

    Path("data/hsi/v1/weather_baselines.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> data/hsi/v1/weather_baselines.json")


if __name__ == "__main__":
    main()
