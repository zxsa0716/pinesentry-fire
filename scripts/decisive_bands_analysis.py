"""Per-band correlation with burn label — Tanager-decisive-bands case.

For each EMIT band (285), compute the AUC of using that single band's
reflectance as a fire predictor on Uiseong. Plot AUC vs wavelength to
identify which spectral regions carry the signal — confirms or
challenges the v4.1 design decision that 1450/1900 nm water absorption
+ 1510/2080 nm foliar N + 700-740 nm REIP are the decisive bands.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
PERI = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
OUT = Path("data/hsi/v1/decisive_bands.png")


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def main():
    if not EMIT_NC.exists():
        print(f"missing {EMIT_NC}", file=sys.stderr); return
    rfl_ds = xr.open_dataset(EMIT_NC, engine="h5netcdf")
    bp = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="location")
    wls = bp.wavelengths.values
    good = bp.good_wavelengths.values.astype(bool)
    rfl = rfl_ds.reflectance.values.astype("float32")
    rfl = np.where(rfl < -1, np.nan, rfl)
    glt_x = loc.glt_x.values; glt_y = loc.glt_y.values

    print(f"EMIT bands: {len(wls)} ({wls.min():.1f}-{wls.max():.1f} nm), good: {good.sum()}")

    # Build burn mask in ortho space
    import geopandas as gpd
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    peri = gpd.read_file(PERI)
    print(f"Perimeter CRS: {peri.crs}")
    print(f"Perimeter bounds: {peri.total_bounds}")

    # The EMIT GLT defines an ortho grid in WGS84 implicitly via the lat/lon arrays.
    # We use the lat/lon of pixel 0,0 and a regular step computed from the array.
    lat_full = orthorectify(loc.lat.values, glt_x, glt_y)
    lon_full = orthorectify(loc.lon.values, glt_x, glt_y)
    H, W = glt_x.shape
    # Build a regular WGS84 grid from the 1d sample of orthorectified lat/lon
    lons_1d = np.nanmean(lon_full, axis=0)
    lats_1d = np.nanmean(lat_full, axis=1)
    res_x = abs(np.nanmedian(np.diff(lons_1d)))
    res_y = abs(np.nanmedian(np.diff(lats_1d)))
    transform = from_origin(np.nanmin(lons_1d), np.nanmax(lats_1d), res_x, res_y)

    peri_wgs = peri.to_crs("EPSG:4326")
    burn = rasterize(((g, 1) for g in peri_wgs.geometry if g is not None),
                     out_shape=(H, W), transform=transform, fill=0, dtype="uint8").astype(bool)
    print(f"burn pixels in ortho grid: {burn.sum()}")

    # Subsample pixels for speed (need ~50k samples to cover 285 bands)
    rng = np.random.default_rng(0)
    valid_lat = np.isfinite(lat_full)
    ys, xs = np.where(valid_lat)
    sample_n = min(80_000, len(ys))
    sample_idx = rng.choice(len(ys), sample_n, replace=False)
    samp_y = ys[sample_idx]; samp_x = xs[sample_idx]
    samp_burn = burn[samp_y, samp_x]
    print(f"sampled {sample_n} ortho pixels  (burn: {samp_burn.sum()})")

    # Need swath coords from GLT for these ortho pixels
    swath_y = (glt_y[samp_y, samp_x] - 1).astype(int)
    swath_x = (glt_x[samp_y, samp_x] - 1).astype(int)
    valid_pix = (glt_x[samp_y, samp_x] > 0) & (glt_y[samp_y, samp_x] > 0)
    samp_y = samp_y[valid_pix]; samp_x = samp_x[valid_pix]
    swath_y = swath_y[valid_pix]; swath_x = swath_x[valid_pix]
    samp_burn = samp_burn[valid_pix]

    print(f"valid swath samples: {len(swath_y)}  burn: {samp_burn.sum()}")

    # Per-band AUC
    from sklearn.metrics import roc_auc_score
    aucs = np.full(len(wls), 0.5, dtype="float32")
    y = samp_burn.astype(int)
    if y.sum() < 10 or (y == 0).sum() < 10:
        print("not enough class balance"); return

    for b in range(len(wls)):
        if not good[b]:
            continue
        s = rfl[swath_y, swath_x, b]
        m = np.isfinite(s)
        if m.sum() < 100:
            continue
        try:
            aucs[b] = roc_auc_score(y[m], s[m])
        except Exception:
            pass
    print(f"AUC per band computed.  range: {aucs[good].min():.3f} - {aucs[good].max():.3f}")

    # Plot
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(wls, aucs, color="#a50026", linewidth=1)
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.8)
    ax.set_xlim(wls.min(), wls.max())
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Per-band ROC AUC (single-band fire predictor)")
    ax.set_title("PineSentry-Fire — Tanager-decisive bands analysis (Uiseong, EMIT 285b)")

    # Highlight v4.1 design-decisive regions
    annotations = {
        "REIP 700-740": (700, 740, "#1a9850"),
        "Foliar N 970-1000": (960, 1010, "#74add1"),
        "Water 1190-1230": (1190, 1230, "#74add1"),
        "Water 1450 (microstructure)": (1430, 1480, "#fd8d3c"),
        "Foliar N 1510-1530": (1510, 1530, "#74add1"),
        "Lignin 1690": (1680, 1700, "#984ea3"),
        "Water 1900 (microstructure)": (1880, 1920, "#fd8d3c"),
        "Foliar N 2080-2100": (2080, 2100, "#74add1"),
        "Lignin 2200": (2200, 2220, "#984ea3"),
    }
    for name, (lo, hi, c) in annotations.items():
        ax.axvspan(lo, hi, alpha=0.15, color=c)
        ax.annotate(name, xy=((lo + hi) / 2, 0.95), fontsize=7, ha="center", color=c, rotation=90)

    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved -> {OUT}")

    # Save peaks to JSON
    sorted_bands = np.argsort(-(aucs - 0.5).clip(0))
    top = []
    for b in sorted_bands[:30]:
        if good[b]:
            top.append({"wavelength_nm": float(wls[b]), "auc": float(aucs[b])})
    Path("data/hsi/v1/decisive_bands_top30.json").write_text(json.dumps(top, indent=2))
    print(f"top-30 decisive bands saved")


if __name__ == "__main__":
    main()
