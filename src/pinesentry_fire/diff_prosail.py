"""Differentiable PROSAIL/4SAIL2 wrapper for dual-branch reconstruction loss.

Skeleton — full implementation in notebook 03_engine_training.ipynb using
prosail-pytorch (jgomezdans/prosail with autograd fork; Wocher et al. 2020).
"""
from __future__ import annotations

import torch
import torch.nn as nn


class DiffPROSAIL(nn.Module):
    """Differentiable PROSPECT-D + 4SAIL2 forward model.

    Inputs (per pixel):
        N        — leaf structure parameter
        Cab      — chlorophyll a+b (μg/cm²)
        Car      — carotenoids (μg/cm²)
        Cw       — equivalent water thickness (cm)
        Cm       — leaf mass per area (g/cm²)
        LAI      — leaf area index
        LIDFa    — leaf inclination
        psoil    — soil background

    Output:
        reflectance(λ) at 5 nm grid 380-2500 nm (426 bands)
    """

    def __init__(self, wavelengths_nm: torch.Tensor, conifer_mode: bool = False):
        super().__init__()
        self.register_buffer("wavelengths", wavelengths_nm)
        self.conifer_mode = conifer_mode

    def forward(self, traits: dict[str, torch.Tensor]) -> torch.Tensor:
        """Forward simulate reflectance from trait map.

        Args:
            traits: dict with keys {N, Cab, Car, Cw, Cm, LAI, LIDFa, psoil}
                    each a (B, H, W) tensor.

        Returns:
            reflectance: (B, n_bands, H, W)

        Implementation notes:
            - Use jgomezdans/prosail Python implementation, ported to PyTorch
              autograd via torch.func.vmap on per-pixel inversion.
            - For conifer_mode, use 4SAIL2 with leaf-clumping factor and N>2.
            - Wocher et al. 2020 (doi:10.3390/rs12101452) provides the
              differentiable forward chain.
        """
        raise NotImplementedError(
            "DiffPROSAIL forward — implement in notebooks/03_engine_training.ipynb. "
            "Use prosail Python lib + torch.func.vmap for per-pixel autograd."
        )


def reconstruction_loss(
    pred_refl: torch.Tensor,
    true_refl: torch.Tensor,
    band_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    """Reconstruction loss between PROSAIL forward and observed reflectance.

    Optional per-band weighting to up-weight SWIR1/SWIR2 (decisive bands).
    """
    diff = (pred_refl - true_refl) ** 2
    if band_weights is not None:
        diff = diff * band_weights.view(1, -1, 1, 1)
    return diff.mean()
