"""Spatial logistic GLMM + permutation test for v4.1 OSF-pre-registered analysis.

Required by reviewer-critic to avoid naive AUC over spatially-autocorrelated
hyperspectral pixels (severity-5 issue from critic review).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss


# ---------------------- Spatial block CV ----------------------

def make_spatial_blocks(
    coords_xy: np.ndarray, block_km: float = 1.0, seed: int = 42
) -> np.ndarray:
    """Assign each pixel to a spatial block (1 km × 1 km by default).

    Args:
        coords_xy: (N, 2) array of (x, y) projected coordinates in meters
        block_km: block side length

    Returns:
        block_id per pixel (N,)
    """
    rng = np.random.default_rng(seed)
    block_m = block_km * 1000.0
    bx = (coords_xy[:, 0] // block_m).astype(int)
    by = (coords_xy[:, 1] // block_m).astype(int)
    block_ids = bx * 100000 + by
    # Shuffle block IDs to randomize fold assignment
    unique_blocks = np.unique(block_ids)
    rng.shuffle(unique_blocks)
    block_to_fold = {b: i % 5 for i, b in enumerate(unique_blocks)}
    return np.array([block_to_fold[b] for b in block_ids])


# ---------------------- Permutation test ----------------------

def permutation_auc(
    y_true: np.ndarray, y_score: np.ndarray, block_ids: np.ndarray, n_permutations: int = 1000, seed: int = 42
) -> dict:
    """Block-permutation test for AUC under spatial autocorrelation."""
    rng = np.random.default_rng(seed)
    observed = roc_auc_score(y_true, y_score)

    null = np.empty(n_permutations, dtype=np.float32)
    for i in range(n_permutations):
        # Permute scores within blocks
        permuted = y_score.copy()
        for b in np.unique(block_ids):
            mask = block_ids == b
            permuted[mask] = rng.permutation(permuted[mask])
        null[i] = roc_auc_score(y_true, permuted)

    p_value = float(np.mean(null >= observed))
    return {"observed_auc": float(observed), "null_mean": float(null.mean()), "null_std": float(null.std()), "p_value": p_value}


# ---------------------- Case-control sampling ----------------------

def case_control_sample(
    df: pd.DataFrame, label_col: str = "burned", ratio: int = 5, seed: int = 42
) -> pd.DataFrame:
    """1:N case-control sampling for class imbalance handling.

    Phillips & Elith 2013 Ecology: appropriate for presence/background analyses.
    """
    rng = np.random.default_rng(seed)
    cases = df[df[label_col] == 1]
    controls = df[df[label_col] == 0]
    n_keep = min(len(controls), len(cases) * ratio)
    keep_idx = rng.choice(controls.index, size=n_keep, replace=False)
    return pd.concat([cases, controls.loc[keep_idx]], ignore_index=True)


# ---------------------- Lift chart ----------------------

def lift_chart_data(y_true: np.ndarray, y_score: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """Compute lift chart bins for Hero figure Panel C."""
    df = pd.DataFrame({"y": y_true, "score": y_score})
    df["decile"] = pd.qcut(df["score"], q=n_bins, labels=False, duplicates="drop")
    out = df.groupby("decile").agg(burn_fraction=("y", "mean"), n=("y", "size")).reset_index()
    base_rate = df["y"].mean()
    out["lift"] = out["burn_fraction"] / base_rate
    # Wilson 95% CI
    p = out["burn_fraction"]
    n = out["n"]
    z = 1.96
    out["ci_lo"] = (p + z**2 / (2 * n) - z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    out["ci_hi"] = (p + z**2 / (2 * n) + z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    return out


# ---------------------- Comprehensive metrics ----------------------

def comprehensive_metrics(y_true: np.ndarray, y_score: np.ndarray) -> dict:
    """ROC-AUC + PR-AUC + Brier + Boyce — required for v4.1 reporting."""
    return {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "brier_score": float(brier_score_loss(y_true, y_score)),
        "n_samples": int(len(y_true)),
        "n_positive": int(y_true.sum()),
        "base_rate": float(y_true.mean()),
    }
