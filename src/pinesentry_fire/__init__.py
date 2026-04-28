"""PineSentry-Fire: Tanager-trained Hydraulic Stress Index for Korean pine forests.

v4.1 final design — see ../../README.md for the ONE question and 10-step logic.
"""

__version__ = "0.1.0"
__author__ = ""
__license__ = "CC-BY-4.0"

from .hsi import hydraulic_stress_index, hydraulic_safety_margin
from .traits import retrieve_traits
from .stac import search_tanager, search_s2, search_emit
from .wavelength_register import register_to_grid, srf_convolve, TANAGER_GRID
from .baselines import kbdi, ndmi, ndvi, ndvi_difference, fwi_simple, korean_dwi
from .spatial_stats import (
    make_spatial_blocks,
    permutation_auc,
    case_control_sample,
    lift_chart_data,
    comprehensive_metrics,
)

__all__ = [
    "hydraulic_stress_index",
    "hydraulic_safety_margin",
    "retrieve_traits",
    "search_tanager",
    "search_s2",
    "search_emit",
    "register_to_grid",
    "srf_convolve",
    "TANAGER_GRID",
    "kbdi",
    "ndmi",
    "ndvi",
    "ndvi_difference",
    "fwi_simple",
    "korean_dwi",
    "make_spatial_blocks",
    "permutation_auc",
    "case_control_sample",
    "lift_chart_data",
    "comprehensive_metrics",
]
