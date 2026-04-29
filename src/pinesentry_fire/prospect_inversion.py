"""PROSPECT-D inversion for EMIT spectra → leaf trait maps.

Replaces the empirical NDII → EWT and NDVI → LMA proxies of v0 with a
physics-based inversion: given leaf reflectance R(lambda), find the
PROSPECT-D parameters (N, Cab, Cw, Cm, Car) that best reproduce R.

Uses the `prosail` Python package (Feret et al. 2008/2017).

Workflow:
    1. EMIT 285-band reflectance spectrum, mask absorption-bad bands.
    2. Resample PROSPECT-D 1-nm output to EMIT band centers via FWHM.
    3. Per-pixel L-BFGS-B inversion (Cab, Cw, Cm, N free; Car=8 fixed).
    4. Save Cab/Cw/Cm rasters → use Cm as LMA, Cw·1e4 as EWT (mm).

Caveat: per-pixel inversion is slow (O(seconds) per pixel). For a
2k×2k EMIT scene this is impractical — instead we sample a sparse
training grid and learn an MLP from R → (LMA, EWT, Cab) over the
sample, then apply the MLP to the full scene.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import NamedTuple

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)


class ProspectParams(NamedTuple):
    N: float = 1.5     # leaf structure
    Cab: float = 40    # chlorophyll a+b (μg/cm²)
    Car: float = 8     # carotenoids
    Cbrown: float = 0  # brown pigments
    Cw: float = 0.012  # equivalent water thickness (cm)  <-> EWT (mm) = Cw * 10
    Cm: float = 0.009  # dry matter / LMA (g/cm²)         <-> LMA (g/m²) = Cm * 1e4
    Anth: float = 0    # anthocyanins


def prospect_d_forward(p: ProspectParams):
    """Run PROSPECT-D and return (wls_nm, reflectance, transmittance) arrays."""
    import prosail
    # prosail.run_prospect returns (wls, R, T) for PROSPECT-D when prospect_version='D'
    out = prosail.run_prospect(
        p.N, p.Cab, p.Car, p.Cbrown, p.Cw, p.Cm,
        ant=p.Anth, prospect_version="D"
    )
    if isinstance(out, tuple) and len(out) == 3:
        wls, R, T = out
    else:
        # Some prosail versions return (R, T) — synthesize wavelengths 400-2500 @ 1nm
        R, T = out[:2]
        wls = np.arange(400, 2501)
    return np.asarray(wls), np.asarray(R), np.asarray(T)


def resample_prospect_to_emit(prospect_wls, prospect_R, emit_centers, emit_fwhm):
    """Convolve PROSPECT 1-nm output with EMIT Gaussian SRFs."""
    out = np.zeros(len(emit_centers), dtype="float32")
    for i, (c, w) in enumerate(zip(emit_centers, emit_fwhm)):
        sigma = w / 2.355   # FWHM -> sigma
        weights = np.exp(-0.5 * ((prospect_wls - c) / sigma) ** 2)
        weights /= weights.sum() + 1e-9
        out[i] = float(np.sum(weights * prospect_R))
    return out


def invert_one(R_obs: np.ndarray, emit_centers: np.ndarray, emit_fwhm: np.ndarray,
                good_band_mask: np.ndarray | None = None,
                init: ProspectParams = ProspectParams()) -> ProspectParams:
    """Single-pixel L-BFGS-B inversion of PROSPECT-D."""
    from scipy.optimize import minimize

    if good_band_mask is None:
        good_band_mask = np.isfinite(R_obs)

    def loss(theta):
        N, Cab, Cw, Cm = theta
        try:
            wls, R, _ = prospect_d_forward(ProspectParams(N=N, Cab=Cab, Cw=Cw, Cm=Cm))
            R_em = resample_prospect_to_emit(wls, R, emit_centers, emit_fwhm)
            diff = (R_em[good_band_mask] - R_obs[good_band_mask]).astype("float32")
            return float(np.sqrt(np.mean(diff ** 2)))
        except Exception:
            return 1e6

    bounds = [(1.0, 3.5), (5, 100), (0.001, 0.05), (0.001, 0.04)]
    x0 = [init.N, init.Cab, init.Cw, init.Cm]
    res = minimize(loss, x0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 25, "gtol": 1e-3})
    return ProspectParams(N=res.x[0], Cab=res.x[1], Cw=res.x[2], Cm=res.x[3])


def build_training_lookup(n_samples: int = 5000, seed: int = 0) -> dict:
    """Generate (params, EMIT-resampled reflectance) pairs to train an MLP."""
    rng = np.random.default_rng(seed)
    Ns   = rng.uniform(1.0, 2.5, n_samples)
    Cabs = rng.uniform(10, 80, n_samples)
    Cws  = rng.uniform(0.002, 0.04, n_samples)
    Cms  = rng.uniform(0.002, 0.025, n_samples)
    return {"N": Ns, "Cab": Cabs, "Cw": Cws, "Cm": Cms}


def emit_band_grid(rfl_nc: Path):
    import xarray as xr
    bp = xr.open_dataset(rfl_nc, engine="h5netcdf", group="sensor_band_parameters")
    return bp.wavelengths.values, bp.fwhm.values, bp.good_wavelengths.values.astype(bool)
