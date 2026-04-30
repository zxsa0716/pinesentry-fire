"""Multi-temporal pre-fire HSI trajectory at Sancheong.

We have THREE EMIT acquisitions for Sancheong:
  2024-12-19  (T-15 mo before 2026-03 fire)
  2026-02-10  (T-1.5 mo)
  2026-03-24  (T-0; fire ignites 2026-03-21, this is T+3 days)

For each acquisition we compute the firerisk_v0 (NDII/NDVI/RE-based) on
the same EMIT footprint, intersect with the 2026-03 dNBR perimeter
polygon, and report:

  - mean firerisk_v0 over the burn footprint
  - mean firerisk_v0 over the unburned reference area
  - separability (Mann-Whitney p)

The hypothesis: the burn-vs-unburned firerisk differential should
INCREASE as the fire approaches. This validates the pre-fire predictability
claim.

Output: data/hsi/v1/sancheong_temporal.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

SCENES = {
    "T-15mo_2024-12-19": "data/emit/sancheong/EMIT_L2A_RFL_001_20241219T032003_2435402_004.nc",
    "T-1.5mo_2026-02-10": "data/emit/sancheong/EMIT_L2A_RFL_001_20260210T054113_2604104_011.nc",
    "T+3d_2026-03-24":   "data/emit/sancheong/EMIT_L2A_RFL_001_20260324T054026_2608303_045.nc",
}
PERI = Path("data/fire_perimeter/synth_sancheong_dnbr.gpkg")
OUT = Path("data/hsi/v1/sancheong_temporal.json")


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def nearest_band(wls, target):
    return int(np.argmin(np.abs(wls - target)))


def main():
    if not PERI.exists():
        print(f"missing {PERI}", file=sys.stderr); return

    import geopandas as gpd
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    from scipy.stats import mannwhitneyu

    peri = gpd.read_file(PERI).to_crs("EPSG:4326")

    summary = {"perimeter_n_features": int(len(peri))}
    summary["scenes"] = {}

    for name, path in SCENES.items():
        p = Path(path)
        if not p.exists():
            print(f"  {name}: missing {p}"); continue

        rfl_ds = xr.open_dataset(p, engine="h5netcdf")
        bp = xr.open_dataset(p, engine="h5netcdf", group="sensor_band_parameters")
        loc = xr.open_dataset(p, engine="h5netcdf", group="location")
        wls = bp.wavelengths.values
        rfl = rfl_ds.reflectance.values.astype("float32")
        rfl = np.where(rfl < -1, np.nan, rfl)

        # NDVI = (NIR - Red) / (NIR + Red); NDII = (NIR - SWIR1640) / (NIR + SWIR1640)
        b_red = nearest_band(wls, 663)
        b_nir = nearest_band(wls, 858)
        b_swir = nearest_band(wls, 1640)
        ndvi = (rfl[..., b_nir] - rfl[..., b_red]) / (rfl[..., b_nir] + rfl[..., b_red] + 1e-6)
        ndii = (rfl[..., b_nir] - rfl[..., b_swir]) / (rfl[..., b_nir] + rfl[..., b_swir] + 1e-6)
        firerisk = 0.6 * (1 - percentile_norm(ndii)) + 0.4 * (1 - percentile_norm(ndvi))

        # Orthorectify
        glt_x = loc.glt_x.values; glt_y = loc.glt_y.values
        fr_o = orthorectify(firerisk, glt_x, glt_y)
        lat_o = orthorectify(loc.lat.values, glt_x, glt_y)
        lon_o = orthorectify(loc.lon.values, glt_x, glt_y)

        lons_1d = np.nanmean(lon_o, axis=0)
        lats_1d = np.nanmean(lat_o, axis=1)
        res_x = abs(np.nanmedian(np.diff(lons_1d)))
        res_y = abs(np.nanmedian(np.diff(lats_1d)))
        transform = from_origin(np.nanmin(lons_1d), np.nanmax(lats_1d), res_x, res_y)

        burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                         out_shape=fr_o.shape, transform=transform,
                         fill=0, dtype="uint8").astype(bool)

        valid = np.isfinite(fr_o)
        burned = fr_o[burn & valid]
        unburned = fr_o[(~burn) & valid]
        if len(burned) < 5 or len(unburned) < 5:
            print(f"  {name}: not enough samples (b={len(burned)}, u={len(unburned)})")
            continue
        mw = mannwhitneyu(burned, unburned, alternative="greater")
        summary["scenes"][name] = {
            "n_burn_pixels_in_scene": int(len(burned)),
            "n_unburn_pixels": int(len(unburned)),
            "mean_firerisk_burned": float(burned.mean()),
            "mean_firerisk_unburned": float(unburned.mean()),
            "delta_burned_minus_unburned": float(burned.mean() - unburned.mean()),
            "mw_u_stat": float(mw.statistic),
            "mw_p": float(mw.pvalue),
        }
        print(f"  {name}: n_burn={len(burned)} burn={burned.mean():.3f} unburn={unburned.mean():.3f} "
              f"delta={burned.mean()-unburned.mean():+.4f} p={mw.pvalue:.2e}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
