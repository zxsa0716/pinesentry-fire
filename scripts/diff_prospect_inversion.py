"""DiffPROSAIL-equivalent gradient-based inversion (v4.1 A3 ablation).

The original v4.1 spec called for a differentiable PROSAIL forward
(implemented in PyTorch / JAX) for end-to-end gradient-based inversion.
Since torch is not installed in this environment, we substitute with
`scipy.optimize.minimize` + the prosail Python package: per-pixel
non-linear least-squares inversion using BFGS gradient descent on a
sampled set of EMIT pixels at Uiseong.

This is the same fitting principle (gradient-based optimization with
the radiative-transfer forward as the objective) but computed via
finite-difference gradients rather than autograd. It is slower than
torch-based DiffPROSAIL but mathematically equivalent.

Compares:
  v2 (MLP leaf inversion)   AUC 0.648 (existing)
  v2.5 (MLP canopy)         AUC 0.608 (existing)
  v2.7 (gradient leaf, A3)  AUC ?     (this script)

Output: data/hsi/v2_7/uiseong_diff_prospect_traits.npz + auc_v2_7.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
PERI    = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
STACK   = Path("data/features/uiseong_stack.tif")
OUT_DIR = Path("data/hsi/v2_7")

N_SAMPLE = 1500   # gradient inversion is slow — 1500 sampled pixels


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not EMIT_NC.exists():
        print(f"missing {EMIT_NC}", file=sys.stderr); return

    import prosail
    from scipy.optimize import minimize
    import xarray as xr

    rfl_ds = xr.open_dataset(EMIT_NC, engine="h5netcdf")
    bp = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="location")
    wls = bp.wavelengths.values
    fwhm = bp.fwhm.values
    good = bp.good_wavelengths.values.astype(bool)
    rfl = rfl_ds.reflectance.values.astype("float32")
    rfl = np.where(rfl < -1, np.nan, rfl)
    H_sw, W_sw, B = rfl.shape
    print(f"EMIT swath {H_sw}x{W_sw}x{B}, good {good.sum()}")

    # PROSPECT-D forward at 1nm grid, resampled to EMIT good bands
    p_wls = np.arange(400, 2501, dtype="float32")
    good_wls = wls[good]
    good_fwhm = fwhm[good]
    sigmas = good_fwhm / 2.355
    # Pre-compute resampling weights matrix (n_good_bands, 2101)
    W = np.zeros((good.sum(), len(p_wls)), dtype="float32")
    for j, (c, sigma) in enumerate(zip(good_wls, sigmas)):
        w = np.exp(-0.5 * ((p_wls - c) / sigma) ** 2)
        w /= w.sum() + 1e-9
        W[j] = w

    def prospect_emit(N, Cab, Car, Cw, Cm):
        rho_t, _ = prosail.run_prospect(N, Cab, Car, 0.0, Cw, Cm, prospect_version="D")
        # rho_t is (2101,) array; resample to EMIT good bands
        return W @ rho_t

    def loss(theta, target):
        N, Cab, Car, Cw, Cm = theta
        # Bound check
        if not (1.0 <= N <= 3.0 and 5 <= Cab <= 100 and 1 <= Car <= 20
                and 0.001 <= Cw <= 0.05 and 0.001 <= Cm <= 0.025):
            return 1e6
        try:
            pred = prospect_emit(N, Cab, Car, Cw, Cm)
        except Exception:
            return 1e6
        residual = pred - target
        return float(np.sum(residual ** 2))

    # Sample valid pixels; preferentially keep many BURN pixels
    import geopandas as gpd
    from rasterio.features import rasterize
    import rioxarray as rxr
    da_stack = rxr.open_rasterio(STACK, masked=True)
    peri = gpd.read_file(PERI).to_crs(da_stack.rio.crs)
    burn_or = rasterize(((g, 1) for g in peri.geometry if g is not None),
                        out_shape=da_stack.shape[1:], transform=da_stack.rio.transform(),
                        fill=0, dtype="uint8").astype(bool)

    # Map back from ortho to swath via GLT
    glt_x = loc.glt_x.values; glt_y = loc.glt_y.values
    H_or, W_or = burn_or.shape
    ys_or = np.arange(min(H_or, glt_x.shape[0]))
    xs_or = np.arange(min(W_or, glt_x.shape[1]))
    # Subsample 1500 pixels balanced across burn (~750) + unburn (~750)
    rng = np.random.default_rng(0)
    valid_glt = (glt_x[:H_or, :W_or] > 0) & (glt_y[:H_or, :W_or] > 0)
    burn_in_glt = burn_or[:glt_x.shape[0], :glt_x.shape[1]] & valid_glt
    unburn_in_glt = (~burn_or[:glt_x.shape[0], :glt_x.shape[1]]) & valid_glt
    burn_idx = np.column_stack(np.where(burn_in_glt))
    unburn_idx = np.column_stack(np.where(unburn_in_glt))
    n_b = min(750, len(burn_idx)); n_u = min(N_SAMPLE - n_b, len(unburn_idx))
    sel_b = burn_idx[rng.choice(len(burn_idx), n_b, replace=False)]
    sel_u = unburn_idx[rng.choice(len(unburn_idx), n_u, replace=False)]
    sel = np.vstack([sel_b, sel_u])
    is_burn = np.concatenate([np.ones(n_b, dtype=bool), np.zeros(n_u, dtype=bool)])
    print(f"sampled {len(sel)} pixels  burn={is_burn.sum()}  unburn={(~is_burn).sum()}")

    # Map to swath
    sw_y = (glt_y[sel[:, 0], sel[:, 1]] - 1).astype(int)
    sw_x = (glt_x[sel[:, 0], sel[:, 1]] - 1).astype(int)
    targets_full = rfl[sw_y, sw_x][:, good]
    keep = np.all(np.isfinite(targets_full), axis=1)
    targets = targets_full[keep]
    is_burn = is_burn[keep]
    print(f"valid spectra: {len(targets)}")

    x0 = np.array([1.5, 40.0, 8.0, 0.012, 0.009])
    bounds = [(1.0, 3.0), (5, 100), (1, 20), (0.001, 0.05), (0.001, 0.025)]
    out_traits = np.zeros((len(targets), 5), dtype="float32")
    for i, t in enumerate(targets):
        if i % 200 == 0:
            print(f"  pixel {i}/{len(targets)}")
        try:
            res = minimize(loss, x0, args=(t,), method="L-BFGS-B",
                           bounds=bounds, options={"maxiter": 30, "ftol": 1e-3})
            out_traits[i] = res.x
        except Exception:
            out_traits[i] = np.nan

    # Build firerisk_diff = 0.5*(1-EWT_n) + 0.3*LMA_n + 0.2*(1-Cab_n)
    Cab = out_traits[:, 1]; Cw = out_traits[:, 3]; Cm = out_traits[:, 4]
    LMA = Cm * 1e4   # convert to g/m²
    EWT = Cw * 10    # convert to mm
    def pn(a):
        m = np.isfinite(a)
        if m.sum() < 5: return np.zeros_like(a)
        plo, phi = np.nanpercentile(a[m], [5, 95])
        if phi <= plo: return np.zeros_like(a)
        return np.clip((a - plo) / (phi - plo), 0, 1)
    fr_diff = 0.5 * (1 - pn(EWT)) + 0.3 * pn(LMA) + 0.2 * (1 - pn(Cab))

    from sklearn.metrics import roc_auc_score
    try:
        auc_diff = float(roc_auc_score(is_burn.astype(int), fr_diff))
    except Exception:
        auc_diff = None
    print(f"\nDiffPROSPECT firerisk AUC on {len(is_burn)} sampled pixels = {auc_diff}")
    Path(OUT_DIR / "auc_v2_7.json").write_text(json.dumps({
        "n_pixels": int(len(is_burn)),
        "n_burn": int(is_burn.sum()),
        "n_unburn": int((~is_burn).sum()),
        "auc_diff_prospect": auc_diff,
        "comparison": {
            "v0_empirical": 0.697,
            "v1_full_HSI": 0.747,
            "v2_MLP_leaf": 0.648,
            "v2_5_MLP_canopy": 0.608,
            "v2_7_diff_prospect_leaf": auc_diff,
        },
        "method": "scipy.optimize.minimize L-BFGS-B PROSPECT-D inversion (DiffPROSAIL stand-in via finite-difference gradient)",
    }, indent=2))
    np.savez(OUT_DIR / "uiseong_diff_prospect_traits.npz",
             traits=out_traits, is_burn=is_burn,
             trait_names=np.array(["N", "Cab", "Car", "Cw", "Cm"]))


if __name__ == "__main__":
    main()
