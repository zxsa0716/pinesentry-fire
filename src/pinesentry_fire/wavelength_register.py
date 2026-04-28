"""Wavelength registration to a common 5 nm grid for cross-sensor harmonization.

Tanager: ~5 nm sampling, 380-2500 nm, ~426 bands (target grid)
EMIT:    ~7.4 nm sampling, 380-2500 nm, ~285 bands (upsample to 5 nm)
Hyperion: ~10 nm sampling, 400-2500 nm, ~220 bands (upsample to 5 nm)
"""
from __future__ import annotations

import numpy as np
import xarray as xr
from scipy.interpolate import CubicSpline

TANAGER_GRID = np.arange(380, 2500 + 5, 5, dtype=np.float32)


def register_to_grid(
    refl: xr.DataArray,
    src_wavelengths_nm: np.ndarray,
    target_grid_nm: np.ndarray = TANAGER_GRID,
    method: str = "cubic",
) -> xr.DataArray:
    """Resample a hyperspectral cube to a common wavelength grid.

    Args:
        refl: (band, y, x) surface reflectance
        src_wavelengths_nm: original wavelength centers
        target_grid_nm: output wavelength centers (default Tanager 5 nm)
        method: 'cubic' / 'linear'

    Returns:
        Resampled DataArray with new band dimension matching target_grid_nm.
    """
    src_wl = np.asarray(src_wavelengths_nm, dtype=np.float32)
    tgt_wl = np.asarray(target_grid_nm, dtype=np.float32)

    if method == "cubic":
        # Per-pixel cubic spline along wavelength axis
        def interp_pixel(spectrum):
            cs = CubicSpline(src_wl, spectrum, extrapolate=False)
            return np.where(np.isnan(cs(tgt_wl)), 0, cs(tgt_wl))

        out = np.apply_along_axis(interp_pixel, axis=0, arr=refl.values)
    else:  # linear
        from scipy.interpolate import interp1d

        f = interp1d(src_wl, refl.values, axis=0, bounds_error=False, fill_value=0)
        out = f(tgt_wl)

    return xr.DataArray(
        out.astype(np.float32),
        dims=("band", "y", "x"),
        coords={"wavelength": ("band", tgt_wl)},
    )


def srf_convolve(
    refl: xr.DataArray,
    src_wl: np.ndarray,
    target_centers: np.ndarray,
    target_fwhm: np.ndarray,
) -> xr.DataArray:
    """Spectral Response Function (SRF) convolution for sensor-to-sensor mapping.

    Used during dual-sensor data augmentation (Guanter et al. EMIT 2023 RSE):
    convolve Tanager spectra with EMIT SRF so model trains on both at once.
    """
    out = np.zeros((target_centers.size,) + refl.shape[1:], dtype=np.float32)
    for i, (c, w) in enumerate(zip(target_centers, target_fwhm)):
        sigma = w / (2 * np.sqrt(2 * np.log(2)))
        weights = np.exp(-0.5 * ((src_wl - c) / sigma) ** 2)
        weights /= weights.sum()
        out[i] = np.tensordot(weights, refl.values, axes=([0], [0]))

    return xr.DataArray(
        out, dims=("band", "y", "x"),
        coords={"wavelength": ("band", target_centers), "fwhm": ("band", target_fwhm)},
    )
