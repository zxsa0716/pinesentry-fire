"""Trait retrieval head — DOFA + LoRA + DiffPROSAIL dual-branch (skeleton).

Final implementation in notebooks/03_engine_training.ipynb. This module
provides the API surface; the actual learned weights load from HuggingFace
Hub at inference time.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr


@dataclass
class TraitRetrievalResult:
    """Container for 5-channel trait map + metadata."""
    lma_g_m2: xr.DataArray
    ewt_mm: xr.DataArray
    n_pct: xr.DataArray         # foliar nitrogen, % dry mass
    lignin_pct: xr.DataArray    # lignin, % dry mass
    reip_nm: xr.DataArray       # red-edge inflection point (nm)
    sensor: str
    scene_id: str
    acquisition_date: str


def retrieve_traits(
    reflectance: xr.DataArray,
    wavelength_nm: np.ndarray,
    sensor: str = "tanager",
    backbone_ckpt: str | None = None,
) -> TraitRetrievalResult:
    """Retrieve 5-channel functional traits from a hyperspectral cube.

    Args:
        reflectance: (band, y, x) surface reflectance [0,1]
        wavelength_nm: per-band center wavelengths (nm)
        sensor: 'tanager' / 'emit' / 'hyperion'
        backbone_ckpt: HuggingFace Hub path; if None, uses default v4.1 ckpt

    Returns:
        TraitRetrievalResult with 5 trait DataArrays + metadata.

    NOTE: This is a skeleton. Implementation in 03_engine_training.ipynb.
    During training, DOFA backbone (frozen) + single LoRA rank-16 +
    Wavelength-Prompt Token + DiffPROSAIL recon loss are coupled.
    """
    raise NotImplementedError(
        "Trait retrieval implementation in notebooks/03_engine_training.ipynb "
        "Skeleton placeholder; replace with HuggingFace Hub model load."
    )
