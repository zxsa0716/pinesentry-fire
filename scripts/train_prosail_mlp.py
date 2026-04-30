"""Train CANOPY-level inversion MLP using PROSAIL (PROSPECT-D + 4SAIL).

Replaces the leaf-level PROSPECT MLP with canopy-level reflectance,
which matches the EMIT pixel domain (canopy + understory + soil at
30m). This addresses the v2 underperformance — pure leaf inversion
fails on mixed canopy pixels.

PROSAIL parameters:
  Leaf: N, Cab, Car, Cw, Cm  (PROSPECT-D)
  Canopy: LAI, hot_spot, leaf inclination, sun zenith, view zenith, soil reflectance
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
OUT_DIR = Path("data/prospect")
OUT_DIR.mkdir(parents=True, exist_ok=True)
N_SAMPLES = 1500


def main():
    if not EMIT_NC.exists():
        print(f"missing {EMIT_NC}", file=sys.stderr); return

    import xarray as xr
    bp = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="sensor_band_parameters")
    centers = bp.wavelengths.values
    fwhm = bp.fwhm.values
    good = bp.good_wavelengths.values.astype(bool)
    print(f"EMIT bands: {len(centers)}, good: {good.sum()}")

    import prosail

    rng = np.random.default_rng(42)
    # Leaf params
    Ns   = rng.uniform(1.0, 2.5, N_SAMPLES)
    Cabs = rng.uniform(10, 80, N_SAMPLES)
    Cars = rng.uniform(2, 15, N_SAMPLES)
    Cws  = rng.uniform(0.005, 0.03, N_SAMPLES)
    Cms  = rng.uniform(0.003, 0.020, N_SAMPLES)
    # Canopy params
    LAIs = rng.uniform(0.5, 6.0, N_SAMPLES)
    hots = rng.uniform(0.05, 0.5, N_SAMPLES)
    lidf_a = rng.uniform(-0.5, 0.5, N_SAMPLES)
    psi  = np.full(N_SAMPLES, 0.0)             # relative azimuth
    tts  = rng.uniform(20, 60, N_SAMPLES)      # sun zenith
    tto  = np.full(N_SAMPLES, 5.0)             # view zenith near nadir

    rsoil = rng.uniform(0.5, 1.5, N_SAMPLES)   # soil brightness
    psoil = rng.uniform(0.0, 1.0, N_SAMPLES)   # soil dry-wet mix

    wls = np.arange(400, 2501, dtype="float32")    # PROSAIL output grid (400-2500 @ 1 nm)
    print(f"Forward simulating {N_SAMPLES} PROSAIL canopy spectra (1nm grid {wls[0]}-{wls[-1]} nm)...")
    R_train = np.zeros((N_SAMPLES, len(centers)), dtype="float32")
    valid = np.ones(N_SAMPLES, dtype=bool)
    n_err = 0
    for i in range(N_SAMPLES):
        try:
            R_canopy = prosail.run_prosail(
                Ns[i], Cabs[i], Cars[i], 0.0, Cws[i], Cms[i],   # PROSPECT
                LAIs[i], lidf_a[i], hots[i], tts[i], tto[i], psi[i],
                prospect_version="D",
                rsoil=float(rsoil[i]),
                psoil=float(psoil[i]),
            )
        except Exception as exc:
            valid[i] = False
            n_err += 1
            if n_err <= 3:
                print(f"  sim {i} failed: {exc}", file=sys.stderr)
            continue
        # PROSAIL returns 2101 bands at 1nm (400-2500). Resample to EMIT bands via Gaussian SRF.
        for j, (c, w) in enumerate(zip(centers, fwhm)):
            sigma = w / 2.355
            weights = np.exp(-0.5 * ((wls - c) / sigma) ** 2)
            weights /= weights.sum() + 1e-9
            R_train[i, j] = float(np.sum(weights * R_canopy))

    valid &= np.all(np.isfinite(R_train), axis=1)
    print(f"valid sims: {valid.sum()}")
    R_train = R_train[valid]
    Cms = Cms[valid]; Cws = Cws[valid]; Cabs = Cabs[valid]; LAIs = LAIs[valid]

    # Train MLP
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler

    X = R_train[:, good]
    print(f"X shape: {X.shape}")
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    targets = {
        "LMA_g_m2": Cms * 1e4,
        "EWT_mm": Cws * 10,
        "Cab_ug_cm2": Cabs,
        "LAI": LAIs,
    }
    mlps = {}
    for name, y in targets.items():
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300,
                           early_stopping=True, random_state=0)
        mlp.fit(Xs, y)
        print(f"  {name}: train R² = {mlp.score(Xs, y):.3f}")
        mlps[name] = mlp

    out = OUT_DIR / "mlp_emit_canopy_uiseong.npz"
    saved = dict(
        good_band_mask=good, emit_centers=centers, emit_fwhm=fwhm,
        scaler_mean=scaler.mean_, scaler_scale=scaler.scale_,
        target_names=np.array(list(targets.keys())),
    )
    for k, m in mlps.items():
        for i, w in enumerate(m.coefs_):
            saved[f"{k}_coefs_{i}"] = w
        for i, w in enumerate(m.intercepts_):
            saved[f"{k}_intercepts_{i}"] = w
    np.savez(out, **saved)
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
