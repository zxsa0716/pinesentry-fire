"""Tanager spectral subset ablation (v4.1 A1 + A2) on Palisades.

Compares Tanager 426-band full spectrum vs SWIR-only (1000-2500 nm) vs
VNIR-only (380-1000 nm) vs S2-binned (13 broadband bins) for predicting
the NIFC Palisades 2025 burn perimeter. The original v4.1 design called
for this to test which spectral region is essential.

Output: data/hsi/v1/tanager_spectral_ablation.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

TANAGER_DIR = Path("data/tanager/palisades")
PERI = Path("data/fire_perimeter/nifc_palisades_2025.geojson")
OUT = Path("data/hsi/v1/tanager_spectral_ablation.json")

# Tanager-1 spectral coverage: 380-2500 nm @ ~5 nm sampling, 426 bands.
# Linear sampling assumption: w[i] = 380 + (2500-380) * i / 425
def tanager_wavelengths():
    return 380.0 + (2500.0 - 380.0) * np.arange(426) / 425.0


# S2 broadband bin centers (13 bands; Lake Erie/MSI-spec)
S2_CENTERS = np.array([443, 490, 560, 665, 705, 740, 783, 842, 865, 945, 1375, 1610, 2190], dtype="float32")
S2_FWHM = np.array([20, 65, 35, 30, 15, 15, 20, 115, 20, 20, 30, 90, 180], dtype="float32")


def load_tanager_scene(scene_dir: Path):
    import h5py
    h5 = next(scene_dir.glob("*_basic_sr_hdf5.h5"), None)
    if h5 is None: return None
    with h5py.File(h5, "r") as f:
        sr = f["HDFEOS/SWATHS/HYP/Data Fields/surface_reflectance"][...]
        lat = f["HDFEOS/SWATHS/HYP/Geolocation Fields/Latitude"][...]
        lon = f["HDFEOS/SWATHS/HYP/Geolocation Fields/Longitude"][...]
        cloud = f["HDFEOS/SWATHS/HYP/Data Fields/beta_cloud_mask"][...]
        nodata = f["HDFEOS/SWATHS/HYP/Data Fields/nodata_pixels"][...]
    sr = np.transpose(sr, (1, 2, 0))   # (H, W, bands)
    sr = np.where(sr < -1, np.nan, sr)
    valid = (cloud == 0) & (nodata == 0)
    return {"sr": sr, "lat": lat, "lon": lon, "valid": valid, "scene_id": scene_dir.name}


def s2_bin(sr, wls):
    """Resample Tanager 426b to S2 13b via Gaussian SRF."""
    out = np.zeros(sr.shape[:2] + (len(S2_CENTERS),), dtype="float32")
    for j, (c, w) in enumerate(zip(S2_CENTERS, S2_FWHM)):
        sigma = w / 2.355
        wts = np.exp(-0.5 * ((wls - c) / sigma) ** 2)
        wts /= wts.sum() + 1e-9
        out[..., j] = (sr * wts[None, None, :]).sum(axis=-1)
    return out


def percentile_norm(a, lo=5, hi=95):
    m = np.isfinite(a)
    if m.sum() < 10:
        return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [lo, hi])
    if phi <= plo: return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def fit_logit_get_auc(X_train, y_train, X_test, y_test):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    clf = LogisticRegression(C=1.0, max_iter=300, n_jobs=1)
    clf.fit(X_train, y_train)
    p = clf.predict_proba(X_test)[:, 1]
    return float(roc_auc_score(y_test, p))


def main():
    scenes = sorted(TANAGER_DIR.glob("2024*_4001"))
    print(f"Tanager scenes: {len(scenes)}")
    if not scenes:
        print("no Tanager scenes found", file=sys.stderr); return

    import geopandas as gpd
    peri = gpd.read_file(PERI).to_crs("EPSG:4326")

    wls = tanager_wavelengths()
    swir_mask = wls >= 1000
    vnir_mask = wls < 1000
    print(f"  bands total {len(wls)}  VNIR {vnir_mask.sum()}  SWIR {swir_mask.sum()}")

    # Aggregate samples across pre-fire scenes (Oct/Dec 2024)
    Xs_full, Xs_vnir, Xs_swir, Xs_s2, ys_all = [], [], [], [], []
    rng = np.random.default_rng(0)
    for sd in scenes:
        d = load_tanager_scene(sd)
        if d is None: continue
        if d["valid"].sum() < 1000: continue

        from shapely.geometry import Point
        from shapely.prepared import prep
        # Build a burn mask by per-pixel point-in-polygon (subsample to 5000 valid pixels)
        ys_idx, xs_idx = np.where(d["valid"])
        n = min(5000, len(ys_idx))
        idx = rng.choice(len(ys_idx), n, replace=False)
        sample_y = ys_idx[idx]; sample_x = xs_idx[idx]
        lats = d["lat"][sample_y, sample_x]; lons = d["lon"][sample_y, sample_x]
        union = peri.geometry.union_all() if hasattr(peri.geometry, "union_all") else peri.geometry.unary_union
        pp = prep(union)
        burn = np.array([pp.contains(Point(x, y)) for x, y in zip(lons, lats)])
        if burn.sum() < 5 or (~burn).sum() < 5:
            print(f"  {sd.name}: not enough burn/unburn samples (b={burn.sum()})")
            continue

        sr_full = d["sr"][sample_y, sample_x, :]
        finite = np.all(np.isfinite(sr_full), axis=1)
        sr_full = sr_full[finite]; burn = burn[finite]
        if len(burn) < 50: continue

        sr_full = sr_full.astype("float32")
        sr_vnir = sr_full[:, vnir_mask]
        sr_swir = sr_full[:, swir_mask]
        sr_s2 = s2_bin(sr_full[:, np.newaxis, :].squeeze(1).reshape(-1, 1, 426), wls).reshape(-1, len(S2_CENTERS))

        Xs_full.append(sr_full); Xs_vnir.append(sr_vnir); Xs_swir.append(sr_swir); Xs_s2.append(sr_s2)
        ys_all.append(burn.astype(int))
        print(f"  {sd.name}: kept {len(burn)} samples (burn={burn.sum()})")

    if not ys_all:
        print("no usable samples"); return
    Xs_full = np.concatenate(Xs_full); Xs_vnir = np.concatenate(Xs_vnir)
    Xs_swir = np.concatenate(Xs_swir); Xs_s2 = np.concatenate(Xs_s2); y = np.concatenate(ys_all)

    # 80/20 random split
    perm = rng.permutation(len(y))
    cut = int(0.8 * len(y))
    tr, te = perm[:cut], perm[cut:]

    aucs = {}
    for name, X in [("Tanager_full_426b", Xs_full),
                    ("Tanager_VNIR_only", Xs_vnir),
                    ("Tanager_SWIR_only", Xs_swir),
                    ("S2_binned_13b", Xs_s2)]:
        try:
            auc = fit_logit_get_auc(X[tr], y[tr], X[te], y[te])
        except Exception as e:
            auc = None
            print(f"  {name}: fit fail {e}")
        aucs[name] = auc
        print(f"  {name}: AUC = {auc}")

    summary = {
        "n_total": int(len(y)), "n_burn": int(y.sum()),
        "n_train": int(cut), "n_test": int(len(y) - cut),
        "scenes_used": len(ys_all),
        "aucs": aucs,
        "interpretation": "If full > S2_binned, hyperspectral matters. If full ~ SWIR_only, the SWIR is what drives the signal.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
