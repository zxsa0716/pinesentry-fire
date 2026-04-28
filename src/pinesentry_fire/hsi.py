"""Hydraulic Stress Index (HSI) — v4.1 physiological prior.

Replaces v4 PCA-derived weights with an a priori physiological index based on
the leaf-level hydraulic safety margin (Martin-StPaul et al. 2017 Ecol. Lett.,
doi:10.1111/ele.12851).

Design decision (locked 2026-04-26):
    HSI = w_safety · (1 − HSM_norm)
        + w_water  · (1 − EWT_norm)
        + w_starch · LMA_norm

    HSM = Ψ_min - P_50     [hydraulic safety margin, Martin-StPaul 2017]
                           Both terms are negative MPa values; positive HSM
                           means the operating point sits ABOVE the embolism
                           threshold (safe). Negative HSM = embolizing.

    P_50:  species-specific leaf-water-potential at 50% conductivity loss
           (from TRY DB; for Pinus densiflora ≈ -3.0 MPa)
    Ψ_min: minimum leaf water potential (proxy from PROSPECT-D inversion of EWT)

Weights are LITERATURE CONSENSUS, not data-fit:
    w_safety = 0.5  (Martin-StPaul 2017, Anderegg 2020 Science)
    w_water  = 0.3
    w_starch = 0.2

Pre-register weights on OSF before running on Korean Hero scenes
to prevent post-hoc fitting accusations.
"""
from __future__ import annotations

import numpy as np
import xarray as xr

# Literature-consensus weights — DO NOT TUNE on Korean validation set
W_SAFETY = 0.5
W_WATER = 0.3
W_STARCH = 0.2

# Species-specific P_50 (MPa) from TRY DB / published reviews
P50_DB: dict[str, float] = {
    "pinus_densiflora": -3.0,    # placeholder, update from TRY
    "pinus_koraiensis": -2.8,
    "quercus_mongolica": -2.5,
    "quercus_serrata": -2.6,
    "quercus_variabilis": -2.4,
    "quercus_acutissima": -2.5,
    "default": -2.7,
}


def percentile_normalize(arr: xr.DataArray, lo: float = 5, hi: float = 95) -> xr.DataArray:
    """Robust [0, 1] normalization via percentile clipping.

    Degenerate inputs (single value, all-NaN, or p_lo == p_hi) return
    a zero array of the same shape rather than NaN, so downstream
    operations remain well-defined on small/uniform tiles.
    """
    p_lo, p_hi = np.nanpercentile(arr.values, [lo, hi])
    if not np.isfinite(p_hi) or p_hi <= p_lo:
        return xr.zeros_like(arr)
    return ((arr - p_lo) / (p_hi - p_lo)).clip(0, 1)


def psi_min_from_ewt(ewt_mm: xr.DataArray, c_apop: float = 0.3, c_sym: float = 1.5) -> xr.DataArray:
    """Approximate leaf minimum water potential (MPa) from EWT (mm).

    Simplified empirical relation (Sack & Holbrook 2006 Annu. Rev.):
        Ψ_min ≈ -c_apop / EWT - c_sym

    More rigorous: invert PROSPECT-D for Cw, then convert via leaf turgor.
    For v4.1 we use this approximation; refine in Notebook 04.
    """
    ewt_safe = ewt_mm.where(ewt_mm > 0.05, 0.05)
    return -c_apop / ewt_safe - c_sym


def hydraulic_safety_margin(
    ewt_mm: xr.DataArray,
    species_map: xr.DataArray | None = None,
    p50_default: float = -2.7,
) -> xr.DataArray:
    """Hydraulic safety margin HSM = P_50 - Ψ_min (MPa).

    Higher HSM = safer (more buffer).
    Lower HSM = closer to embolism threshold = HIGH STRESS.

    Args:
        ewt_mm: Equivalent Water Thickness (mm), per pixel.
        species_map: optional categorical map of species (for P_50 lookup).
                     If None, uses p50_default.
        p50_default: fallback P_50 (MPa).

    Returns:
        HSM in MPa, broadcast to ewt_mm shape.
    """
    psi_min = psi_min_from_ewt(ewt_mm)

    if species_map is None:
        p50 = xr.full_like(psi_min, p50_default)
    else:
        # Map species labels → P_50
        p50 = xr.apply_ufunc(
            lambda s: np.vectorize(lambda x: P50_DB.get(str(x), p50_default))(s),
            species_map,
            dask="parallelized",
        )

    return psi_min - p50


def hydraulic_stress_index(
    lma_g_m2: xr.DataArray,
    ewt_mm: xr.DataArray,
    species_map: xr.DataArray | None = None,
    weights: tuple[float, float, float] = (W_SAFETY, W_WATER, W_STARCH),
) -> xr.DataArray:
    """Compute Hydraulic Stress Index (HSI), per-pixel, in [0, 1].

    HSI = w_safety · (1 − HSM_norm) + w_water · (1 − EWT_norm) + w_starch · LMA_norm

    Args:
        lma_g_m2: Leaf Mass per Area (g/m²)
        ewt_mm:   Equivalent Water Thickness (mm)
        species_map: optional categorical species labels per pixel
        weights:  (w_safety, w_water, w_starch); default LITERATURE CONSENSUS.
                  DO NOT tune on Korean validation set — pre-register on OSF.

    Returns:
        HSI in [0, 1]. Higher = more hydraulically stressed = higher fire risk proxy.
    """
    w_safety, w_water, w_starch = weights
    assert abs(sum(weights) - 1.0) < 1e-6, "Weights must sum to 1"

    hsm = hydraulic_safety_margin(ewt_mm, species_map)
    hsm_norm = percentile_normalize(hsm)
    ewt_norm = percentile_normalize(ewt_mm)
    lma_norm = percentile_normalize(lma_g_m2)

    hsi = (
        w_safety * (1 - hsm_norm)
        + w_water * (1 - ewt_norm)
        + w_starch * lma_norm
    )
    hsi.attrs["long_name"] = "Hydraulic Stress Index"
    hsi.attrs["units"] = "dimensionless [0,1]"
    hsi.attrs["weights"] = f"safety={w_safety},water={w_water},starch={w_starch}"
    hsi.attrs["reference"] = "Martin-StPaul 2017 Ecol Lett; Anderegg 2020 Science"
    return hsi


def hsi_sensitivity(
    lma_g_m2: xr.DataArray,
    ewt_mm: xr.DataArray,
    species_map: xr.DataArray | None = None,
    weight_perturbation: float = 0.5,
    n_samples: int = 100,
    rng_seed: int = 42,
) -> dict[str, xr.DataArray]:
    """Sensitivity analysis for ablation A6.

    Perturbs the 3 weights by ±weight_perturbation (renormalized to sum to 1),
    samples n_samples random weight combinations, and returns mean and std maps.
    """
    rng = np.random.default_rng(rng_seed)
    base = np.array([W_SAFETY, W_WATER, W_STARCH])
    samples = []

    for _ in range(n_samples):
        delta = rng.uniform(-weight_perturbation, weight_perturbation, size=3) * base
        perturbed = np.clip(base + delta, 0.01, None)
        perturbed /= perturbed.sum()
        hsi = hydraulic_stress_index(
            lma_g_m2, ewt_mm, species_map, tuple(perturbed)
        )
        samples.append(hsi)

    stack = xr.concat(samples, dim="sample")
    return {"mean": stack.mean("sample"), "std": stack.std("sample")}
