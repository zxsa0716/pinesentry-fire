"""Train a PROSPECT-D inversion MLP from forward-model lookup table.

For each EMIT scene we:
  1. Generate N=5000 (params, reflectance) pairs via PROSPECT-D forward
  2. Train MLP: 285-band reflectance -> (LMA, EWT, Cab)
  3. Save to data/prospect/mlp_emit_uiseong.npz (weights + metadata)

The MLP can then be applied per-pixel in O(1) lookup, replacing the
expensive per-pixel L-BFGS-B optimization.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
OUT_DIR = Path("data/prospect")
OUT_DIR.mkdir(parents=True, exist_ok=True)
N_SAMPLES = 1500   # forward simulations


def main():
    if not EMIT_NC.exists():
        print(f"missing {EMIT_NC}", file=sys.stderr); return

    sys.path.insert(0, "src")
    from pinesentry_fire.prospect_inversion import (
        emit_band_grid, prospect_d_forward, resample_prospect_to_emit, ProspectParams
    )

    centers, fwhm, good = emit_band_grid(EMIT_NC)
    print(f"EMIT bands: {len(centers)}, good: {good.sum()}")

    rng = np.random.default_rng(42)
    Ns   = rng.uniform(1.0, 2.5, N_SAMPLES)
    Cabs = rng.uniform(10, 80, N_SAMPLES)
    Cws  = rng.uniform(0.002, 0.04, N_SAMPLES)
    Cms  = rng.uniform(0.002, 0.025, N_SAMPLES)
    print(f"Forward simulating {N_SAMPLES} PROSPECT-D spectra...")

    R_train = np.zeros((N_SAMPLES, len(centers)), dtype="float32")
    for i in range(N_SAMPLES):
        try:
            wls, R, _ = prospect_d_forward(ProspectParams(N=Ns[i], Cab=Cabs[i], Cw=Cws[i], Cm=Cms[i]))
            R_train[i] = resample_prospect_to_emit(wls, R, centers, fwhm)
        except Exception as e:
            print(f"  fail {i}: {e}")
            R_train[i] = np.nan

    valid = np.all(np.isfinite(R_train), axis=1)
    print(f"  valid sims: {valid.sum()} / {N_SAMPLES}")
    R_train = R_train[valid]
    Ns = Ns[valid]; Cabs = Cabs[valid]; Cws = Cws[valid]; Cms = Cms[valid]

    # Train per-target MLPs (smaller, faster to invert)
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler

    X = R_train[:, good]   # only good wavelengths
    print(f"X shape (good bands): {X.shape}")

    targets = {"LMA_g_m2": Cms * 1e4, "EWT_mm": Cws * 10, "Cab_ug_cm2": Cabs}
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    mlps = {}
    for name, y in targets.items():
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300,
                           early_stopping=True, random_state=0)
        mlp.fit(Xs, y)
        score = mlp.score(Xs, y)
        print(f"  {name}: train R² = {score:.3f}")
        mlps[name] = mlp

    out = OUT_DIR / "mlp_emit_uiseong.npz"
    np.savez(
        out,
        good_band_mask=good,
        emit_centers=centers,
        emit_fwhm=fwhm,
        scaler_mean=scaler.mean_,
        scaler_scale=scaler.scale_,
        # serialize each MLP's weights
        **{f"{k}_coefs_{i}": w for k, m in mlps.items() for i, w in enumerate(m.coefs_)},
        **{f"{k}_intercepts_{i}": w for k, m in mlps.items() for i, w in enumerate(m.intercepts_)},
        target_names=np.array(list(targets.keys())),
    )
    print(f"\nsaved -> {out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
