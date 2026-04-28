"""Baseline fire-risk indices for ablation A5 (HSI vs weather/optical baselines).

Required for v4.1 to outperform: KBDI, FWI, DWI, NDMI, NDVI difference.
"""
from __future__ import annotations

import numpy as np
import xarray as xr


def kbdi(precip_mm: xr.DataArray, tmax_c: xr.DataArray, kbdi_prev: xr.DataArray | None = None) -> xr.DataArray:
    """Keetch-Byram Drought Index (Keetch & Byram 1968).

    KBDI ranges 0 (saturated) to 800 (extreme drought).
    Daily input: precipitation (mm), max temperature (°C).
    """
    if kbdi_prev is None:
        kbdi_prev = xr.zeros_like(tmax_c)

    # Net precipitation (above 5.1 mm threshold)
    net_p = (precip_mm - 5.1).clip(min=0)
    # Drought factor (Keetch & Byram empirical)
    df_num = (800 - kbdi_prev) * (0.968 * np.exp(0.0486 * tmax_c) - 8.30) * 0.001
    df_den = 1 + 10.88 * np.exp(-0.0441 * 1.0)  # constant
    df = (df_num / df_den).clip(min=0)

    return (kbdi_prev - net_p + df).clip(0, 800)


def ndmi(refl: xr.DataArray, nir_band: float = 860, swir_band: float = 1640) -> xr.DataArray:
    """Normalized Difference Moisture Index — Sentinel-2 baseline (Gao 1996)."""
    nir = refl.sel(wavelength=nir_band, method="nearest")
    swir = refl.sel(wavelength=swir_band, method="nearest")
    return (nir - swir) / (nir + swir + 1e-9)


def ndvi(refl: xr.DataArray, red_band: float = 670, nir_band: float = 860) -> xr.DataArray:
    """Standard NDVI."""
    r = refl.sel(wavelength=red_band, method="nearest")
    nir = refl.sel(wavelength=nir_band, method="nearest")
    return (nir - r) / (nir + r + 1e-9)


def ndvi_difference(refl_t: xr.DataArray, refl_t_minus: xr.DataArray) -> xr.DataArray:
    """ΔNDVI between two snapshots — burn signal proxy."""
    return ndvi(refl_t) - ndvi(refl_t_minus)


def fwi_simple(temp_c: xr.DataArray, rh_pct: xr.DataArray, wind_kmh: xr.DataArray, precip_mm: xr.DataArray) -> xr.DataArray:
    """Simplified Fire Weather Index (Van Wagner 1987 components, single-day proxy).

    Production-grade FWI requires DC/DMC/FFMC time-series propagation; this is
    a snapshot proxy for ablation A5 baseline comparison.
    """
    # Fine fuel moisture proxy
    ffmc = 101 - 0.5 * (rh_pct + precip_mm * 5)
    # Wind effect
    isi = ffmc * np.exp(0.05 * wind_kmh)
    # Drought factor proxy
    bui = (temp_c + 20) * (1 - rh_pct / 100)
    # Final FWI
    return 0.1 * isi * bui


def korean_dwi(temp_c: xr.DataArray, rh_pct: xr.DataArray, wind_ms: xr.DataArray, days_since_rain: xr.DataArray) -> xr.DataArray:
    """Korean 산림청 Daily Weather Index (Won et al. 2019 한국임학회지).

    Operational index used by 산림청 산불대응센터.
    """
    return 0.5 * temp_c + 0.3 * (100 - rh_pct) + 0.1 * wind_ms + 0.1 * days_since_rain.clip(0, 30)
