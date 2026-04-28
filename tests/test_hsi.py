"""Tests for HSI module — ensures pre-registered weights stay locked."""
from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from pinesentry_fire.hsi import (
    W_SAFETY, W_WATER, W_STARCH,
    P50_DB,
    hydraulic_safety_margin,
    hydraulic_stress_index,
    psi_min_from_ewt,
    percentile_normalize,
)


def make_da(values, dims=("y", "x")):
    arr = np.asarray(values, dtype=np.float32)
    return xr.DataArray(arr, dims=dims)


# --- Locked-weights sanity ---------------------------------------------------

def test_weights_sum_to_one():
    """Pre-registered weights MUST sum to 1.0. Don't change without OSF amendment."""
    assert abs(W_SAFETY + W_WATER + W_STARCH - 1.0) < 1e-6


def test_weights_match_osf_pre_registration():
    """OSF pre-registered values; do not modify without amendment."""
    assert W_SAFETY == 0.5
    assert W_WATER == 0.3
    assert W_STARCH == 0.2


def test_p50_species_db_has_korean_species():
    for sp in ["pinus_densiflora", "pinus_koraiensis", "quercus_mongolica"]:
        assert sp in P50_DB


# --- HSM / Ψ_min sanity ------------------------------------------------------

def test_psi_min_decreases_as_water_decreases():
    """Less water → more negative Ψ_min (more stress)."""
    ewt_high = make_da([0.20])
    ewt_low = make_da([0.05])
    psi_high = psi_min_from_ewt(ewt_high)
    psi_low = psi_min_from_ewt(ewt_low)
    assert float(psi_low) < float(psi_high)


def test_hsm_safer_when_more_water():
    ewt = make_da(np.array([[0.05, 0.10, 0.20]], dtype=np.float32))
    hsm = hydraulic_safety_margin(ewt, p50_default=-3.0)
    # HSM should increase (less negative) with EWT
    vals = hsm.values.ravel()
    assert vals[0] < vals[1] < vals[2]


# --- HSI sanity --------------------------------------------------------------

def test_hsi_in_unit_interval():
    rng = np.random.default_rng(0)
    ewt = make_da(rng.uniform(0.05, 0.25, size=(10, 10)))
    lma = make_da(rng.uniform(50, 200, size=(10, 10)))
    hsi = hydraulic_stress_index(lma, ewt)
    assert hsi.min() >= 0
    assert hsi.max() <= 1


def test_hsi_higher_for_drier_leaves():
    ewt_dry = make_da([[0.05]])
    ewt_wet = make_da([[0.25]])
    lma = make_da([[120.0]])
    hsi_dry = hydraulic_stress_index(lma, ewt_dry)
    hsi_wet = hydraulic_stress_index(lma, ewt_wet)
    assert float(hsi_dry) >= float(hsi_wet)


def test_percentile_normalize_robust():
    arr = make_da([1, 2, 3, 4, 5, 1000])  # outlier
    norm = percentile_normalize(arr)
    assert norm.max() == 1.0
    # Outlier should be clipped to 1
    assert norm.values[-1] == 1.0


# --- Reject post-hoc tuning --------------------------------------------------

def test_rejects_invalid_weights():
    """Weights that don't sum to 1 should fail."""
    ewt = make_da([[0.10]])
    lma = make_da([[100.0]])
    with pytest.raises(AssertionError):
        hydraulic_stress_index(lma, ewt, weights=(0.5, 0.5, 0.5))
