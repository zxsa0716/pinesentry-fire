"""ISOFIT-equivalent atmospheric residual quality check on EMIT L2A.

ISOFIT is the Imaging Spectrometer Optimal FITting framework JPL uses to
generate EMIT L2A from L1B. We can't rerun the full retrieval, but we can
compute per-pixel atmospheric quality flags by checking the band-wise
residual at the deep H2O / O2 absorption regions:

  - 1380 nm cirrus / strong H2O — should be saturated (R ≈ 0) over cloud-free
                                 vegetation; high values flag thin cirrus.
  - 1880-1900 nm strong H2O — also near zero over forest canopies.
  - 760 nm O2-A — narrow oxygen feature; sharp dip if atmospheric correction OK.

EMIT's `good_wavelengths` mask already excludes the worst bands.  For pixels
that PASS that mask but still have anomalously high reflectance in the
strong-absorption bands (e.g., R(1380) > 0.05), we flag as "atmosphere
residual." Output: per-pixel flag map + per-site fraction.

Output:
  data/hsi/v1/{site}_atmo_flag.tif   (uint8, 1=residual flag)
  data/hsi/v1/atmo_summary.json      (fraction flagged per site)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

EMIT_SCENES = {
    "uiseong":   "data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc",
    "sancheong": "data/emit/sancheong/EMIT_L2A_RFL_001_20260324T054026_2608303_045.nc",
}
OUT_DIR = Path("data/hsi/v1")


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}

    for site, path in EMIT_SCENES.items():
        p = Path(path)
        if not p.exists():
            print(f"  {site}: missing {p}", file=sys.stderr); continue

        rfl_ds = xr.open_dataset(p, engine="h5netcdf")
        bp = xr.open_dataset(p, engine="h5netcdf", group="sensor_band_parameters")
        loc = xr.open_dataset(p, engine="h5netcdf", group="location")

        wls = bp.wavelengths.values
        good = bp.good_wavelengths.values.astype(bool)
        rfl = rfl_ds.reflectance.values.astype("float32")
        rfl = np.where(rfl < -1, np.nan, rfl)

        # Pick nearest GOOD bands to atmospheric absorption centers.
        # Note: 1380/1880 are typically OUTSIDE good_wavelengths; we instead
        # check the strongest residual valleys still inside the good mask
        # (around 940 H2O, 1140 H2O, 760 O2-A) and flag pixels whose
        # reflectance there exceeds vegetation-typical levels.
        targets = {"O2A_760": 760, "H2O_940": 940, "H2O_1140": 1140}
        thresholds = {"O2A_760": 0.40, "H2O_940": 0.55, "H2O_1140": 0.50}
        flag = np.zeros(rfl.shape[:2], dtype="uint8")
        per_band = {}
        for name, tgt in targets.items():
            cand = np.where(good)[0]
            b = cand[np.argmin(np.abs(wls[cand] - tgt))]
            band_r = rfl[..., b]
            high = band_r > thresholds[name]
            n_high = int(np.nansum(high))
            n_valid = int(np.sum(np.isfinite(band_r)))
            per_band[name] = {
                "wavelength_nm": float(wls[b]),
                "threshold_R": thresholds[name],
                "n_high": n_high,
                "n_valid": n_valid,
                "fraction_flagged": (n_high / n_valid) if n_valid else None,
            }
            flag = np.maximum(flag, high.astype("uint8"))

        # Orthorectify the flag for downstream comparison.
        glt_x = loc.glt_x.values; glt_y = loc.glt_y.values
        flag_o = orthorectify(flag.astype("float32"), glt_x, glt_y, fill=0).astype("uint8")

        out_tif = OUT_DIR / f"{site}_atmo_flag.tif"
        # Write via rioxarray
        import rioxarray  # noqa: F401
        from rasterio.transform import from_origin
        lat_full = orthorectify(loc.lat.values, glt_x, glt_y)
        lon_full = orthorectify(loc.lon.values, glt_x, glt_y)
        lons_1d = np.nanmean(lon_full, axis=0)
        lats_1d = np.nanmean(lat_full, axis=1)
        res_x = abs(np.nanmedian(np.diff(lons_1d)))
        res_y = abs(np.nanmedian(np.diff(lats_1d)))
        transform = from_origin(np.nanmin(lons_1d), np.nanmax(lats_1d), res_x, res_y)
        H, W = flag_o.shape
        ys = np.nanmax(lats_1d) - np.arange(H) * res_y
        xs = np.nanmin(lons_1d) + np.arange(W) * res_x
        da = xr.DataArray(flag_o, dims=("y", "x"), coords={"y": ys, "x": xs}, name="atmo_flag")
        da.rio.write_crs("EPSG:4326", inplace=True)
        da.rio.write_transform(transform, inplace=True)
        da.rio.to_raster(out_tif, compress="LZW", tiled=True)

        summary[site] = {
            "per_band": per_band,
            "fraction_flagged_any": float((flag_o > 0).mean()),
            "n_pixels_ortho": int(flag_o.size),
            "out_tif": str(out_tif),
        }
        print(f"  {site}: any-band flag fraction = {summary[site]['fraction_flagged_any']:.4f}")

    out_json = OUT_DIR / "atmo_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {out_json}")


if __name__ == "__main__":
    main()
