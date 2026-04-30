"""HSI v2.5 — PROSAIL canopy inversion (PROSPECT-D + 4SAIL).

Replaces the v2 leaf-level PROSPECT inversion with a canopy-level PROSAIL
forward model. Canopy reflectance = leaf optical properties × LAI ×
soil background, which matches what an EMIT pixel actually integrates at
30 m.

Outputs:
  data/hsi/v2_5/uiseong_hsi_v2_5.tif
  data/hsi/v2_5/uiseong_canopy_{LMA,EWT,Cab,LAI}.tif
  data/hsi/v2_5/auc_v2_5.json

firerisk_v2_5 = 0.4·(1-EWT_n) + 0.25·LMA_n + 0.15·(1-Cab_n) + 0.20·(1-LAI_n)

Same OSF v1 fusion weights at the HSI level — only firerisk component
upgraded. Compared against v1 (0.747) and v2 (0.648).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr
import xarray as xr

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
MLP_NPZ = Path("data/prospect/mlp_emit_canopy_uiseong.npz")
PERI    = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
STACK   = Path("data/features/uiseong_stack.tif")
OUT_DIR = Path("data/hsi/v2_5")


def mlp_forward(X, npz, target_prefix):
    coefs = []; intercepts = []
    i = 0
    while f"{target_prefix}_coefs_{i}" in npz:
        coefs.append(npz[f"{target_prefix}_coefs_{i}"])
        intercepts.append(npz[f"{target_prefix}_intercepts_{i}"])
        i += 1
    h = X
    for k, (c, b) in enumerate(zip(coefs, intercepts)):
        h = h @ c + b
        if k < len(coefs) - 1:
            h = np.maximum(0, h)
    return h.ravel()


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo:
        return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def main():
    if not MLP_NPZ.exists():
        print(f"missing {MLP_NPZ} — run train_prosail_mlp.py first", file=sys.stderr); sys.exit(1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    npz = np.load(MLP_NPZ, allow_pickle=True)
    good = npz["good_band_mask"].astype(bool)
    scaler_mean = npz["scaler_mean"]; scaler_scale = npz["scaler_scale"]

    rfl_ds = xr.open_dataset(EMIT_NC, engine="h5netcdf")
    loc = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="location")
    rfl = rfl_ds.reflectance.values.astype("float32")
    rfl = np.where(rfl < -1, np.nan, rfl)
    H_sw, W_sw, B = rfl.shape
    print(f"EMIT swath {H_sw}x{W_sw}x{B}")

    R = rfl.reshape(-1, B)[:, good]
    R_valid = np.all(np.isfinite(R), axis=1)
    R_safe = np.where(R_valid[:, None], R, 0.0)
    Xs = (R_safe - scaler_mean) / scaler_scale

    print("Inferring canopy LMA / EWT / Cab / LAI ...")
    lma  = mlp_forward(Xs, npz, "LMA_g_m2")
    ewt  = mlp_forward(Xs, npz, "EWT_mm")
    cab  = mlp_forward(Xs, npz, "Cab_ug_cm2")
    lai  = mlp_forward(Xs, npz, "LAI")
    lma  = np.where(R_valid, lma, np.nan).reshape(H_sw, W_sw)
    ewt  = np.where(R_valid, ewt, np.nan).reshape(H_sw, W_sw)
    cab  = np.where(R_valid, cab, np.nan).reshape(H_sw, W_sw)
    lai  = np.where(R_valid, lai, np.nan).reshape(H_sw, W_sw)

    # Clip to PROSAIL training bounds
    lma = np.clip(lma, 30.0, 200.0)
    ewt = np.clip(ewt, 0.05, 0.30)
    cab = np.clip(cab, 10.0, 80.0)
    lai = np.clip(lai, 0.5, 6.0)
    print(f"  LMA p50={np.nanpercentile(lma,50):.1f}  EWT p50={np.nanpercentile(ewt,50):.3f}  Cab p50={np.nanpercentile(cab,50):.1f}  LAI p50={np.nanpercentile(lai,50):.2f}")

    glt_x = loc.glt_x.values; glt_y = loc.glt_y.values
    lma_o = orthorectify(lma, glt_x, glt_y)
    ewt_o = orthorectify(ewt, glt_x, glt_y)
    cab_o = orthorectify(cab, glt_x, glt_y)
    lai_o = orthorectify(lai, glt_x, glt_y)

    ewt_n = percentile_norm(ewt_o)
    lma_n = percentile_norm(lma_o)
    cab_n = percentile_norm(cab_o)
    lai_n = percentile_norm(lai_o)
    firerisk_v2_5 = 0.40 * (1 - ewt_n) + 0.25 * lma_n + 0.15 * (1 - cab_n) + 0.20 * (1 - lai_n)

    da_stack = rxr.open_rasterio(STACK, masked=True)
    pyro = da_stack.values[6]
    south = da_stack.values[5]
    pine_tx = pyro * south
    target_shape = pyro.shape

    if firerisk_v2_5.shape != target_shape:
        sy = min(firerisk_v2_5.shape[0], target_shape[0])
        sx = min(firerisk_v2_5.shape[1], target_shape[1])
        new = np.full(target_shape, np.nan, dtype="float32")
        new[:sy, :sx] = firerisk_v2_5[:sy, :sx]
        firerisk_v2_5 = new

    pyro_n  = percentile_norm(pyro)
    south_n = percentile_norm(south)
    fr_n    = percentile_norm(firerisk_v2_5)
    tx_n    = percentile_norm(pine_tx)

    hsi_v2_5 = (0.40 * pyro_n + 0.20 * south_n + 0.30 * fr_n + 0.10 * tx_n)

    out_tif = OUT_DIR / "uiseong_hsi_v2_5.tif"
    da_out = xr.DataArray(hsi_v2_5.astype("float32"), dims=("y", "x"),
                          coords={"y": da_stack.y, "x": da_stack.x}, name="hsi_v2_5")
    da_out.rio.write_crs(da_stack.rio.crs, inplace=True)
    da_out.rio.to_raster(out_tif, compress="LZW", tiled=True)
    print(f"saved -> {out_tif}")

    for name, arr in [("LMA", lma_o), ("EWT", ewt_o), ("Cab", cab_o), ("LAI", lai_o)]:
        if arr.shape != target_shape:
            sy = min(arr.shape[0], target_shape[0])
            sx = min(arr.shape[1], target_shape[1])
            new = np.full(target_shape, np.nan, dtype="float32")
            new[:sy, :sx] = arr[:sy, :sx]
            arr = new
        d = xr.DataArray(arr.astype("float32"), dims=("y", "x"),
                         coords={"y": da_stack.y, "x": da_stack.x}, name=f"canopy_{name}")
        d.rio.write_crs(da_stack.rio.crs, inplace=True)
        d.rio.to_raster(OUT_DIR / f"uiseong_canopy_{name}.tif", compress="LZW", tiled=True)

    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score
    peri = gpd.read_file(PERI).to_crs(da_stack.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=hsi_v2_5.shape, transform=da_stack.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(hsi_v2_5)
    burned = hsi_v2_5[burn & valid]; unburned = hsi_v2_5[(~burn) & valid]
    if len(burned) > 5 and len(unburned) > 5:
        y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
        s = np.concatenate([burned, unburned])
        auc = roc_auc_score(y, s)
        print(f"\nHSI v2.5 AUC = {auc:.4f}  (v1=0.7467, v2=0.648)")
        Path(OUT_DIR / "auc_v2_5.json").write_text(json.dumps(
            {"auc": float(auc), "n_burn": int(len(burned)), "n_unburn": int(len(unburned)),
             "components": "PROSAIL canopy: LMA EWT Cab LAI"}, indent=2))


if __name__ == "__main__":
    main()
