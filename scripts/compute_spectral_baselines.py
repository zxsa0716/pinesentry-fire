"""Compute NDMI, NDVI, NDII spectral baselines vs HSI v1 — A5 ablation.

For each site (Uiseong + Sancheong), reads the EMIT baseline scene and
computes 3 spectral indices, then evaluates each against the dNBR
perimeter exactly as we did for HSI v1.

Output:
  data/baselines/{site}_baselines.tif   (3-band: NDMI, NDVI, NDII)
  data/baselines/{site}_eval.png         (4 ROC curves overlay vs HSI v1)
  data/baselines/{site}_summary.json     (AUC table)

KBDI/FWI/DWI need T/RH/wind/precip which require ERA5 daily — deferred
to v1.5 once climate cube is on disk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rxr
import xarray as xr

EMIT_BY_SITE = {
    "uiseong":   "EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc",
    "sancheong": "EMIT_L2A_RFL_001_20241219T032003_2435402_004.nc",
}
OUT_DIR = Path("data/baselines")


def open_emit(path: Path):
    rfl_ds = xr.open_dataset(path, engine="h5netcdf")
    bp = xr.open_dataset(path, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(path, engine="h5netcdf", group="location")
    return rfl_ds, bp, loc


def nearest(wls, target):
    return int(np.argmin(np.abs(wls - target)))


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def compute_indices(rfl, wls):
    eps = 1e-6
    iR = nearest(wls, 660)
    iN = nearest(wls, 858)
    iS1 = nearest(wls, 1640)
    iS2 = nearest(wls, 2200)
    R = rfl[..., iR]
    N = rfl[..., iN]
    S1 = rfl[..., iS1]
    return {
        "ndvi": (N - R) / (N + R + eps),
        "ndmi": (N - S1) / (N + S1 + eps),
        "ndii": (N - S1) / (N + S1 + eps),  # alias of NDMI for convention
    }


def evaluate_burn(score: np.ndarray, lat, lon, peri_path: Path, hsi_grid):
    """Rasterize perimeter on the same grid; return (AUC, lift10, n_burn, n_unburn, fpr, tpr)."""
    if not peri_path.exists():
        return None
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score, roc_curve

    peri = gpd.read_file(peri_path).to_crs(hsi_grid.rio.crs)
    burn = rasterize(((g, 1) for g in peri.geometry if g is not None),
                     out_shape=score.shape,
                     transform=hsi_grid.rio.transform(),
                     fill=0, dtype="uint8").astype(bool)
    valid = np.isfinite(score)
    burned = score[burn & valid]
    unburned = score[(~burn) & valid]
    if len(burned) == 0 or len(unburned) == 0:
        return None
    y = np.concatenate([np.ones(len(burned)), np.zeros(len(unburned))])
    s = np.concatenate([burned, unburned])
    auc = roc_auc_score(y, s)
    fpr, tpr, _ = roc_curve(y, s)
    order = np.argsort(-s)
    top10 = order[: max(1, len(order) // 10)]
    lift = (y[top10].mean()) / max(y.mean(), 1e-9)
    return {"auc": auc, "lift": lift, "n_burned": len(burned), "n_unburned": len(unburned), "fpr": fpr, "tpr": tpr}


def run_site(site: str):
    em = EMIT_BY_SITE.get(site)
    if not em:
        return None
    emit_path = Path(f"data/emit/{site}/{em}")
    if not emit_path.exists():
        print(f"missing EMIT for {site}: {emit_path}")
        return None

    print(f"\n=== {site} ({em}) ===")
    rfl_ds, bp, loc = open_emit(emit_path)
    wls = bp.wavelengths.values
    rfl = rfl_ds.reflectance.values
    rfl = np.where(rfl < -1, np.nan, rfl)

    idx = compute_indices(rfl, wls)
    glt_x, glt_y = loc.glt_x.values, loc.glt_y.values
    lat = orthorectify(loc.lat.values, glt_x, glt_y)
    lon = orthorectify(loc.lon.values, glt_x, glt_y)

    ortho = {k: orthorectify(v, glt_x, glt_y) for k, v in idx.items()}

    # Reference HSI v1 grid for shape match
    hsi_v1_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
    if not hsi_v1_path.exists():
        print(f"  missing HSI v1 grid: {hsi_v1_path}")
        return None
    da_ref = rxr.open_rasterio(hsi_v1_path, masked=True).squeeze()
    H, W = da_ref.shape

    # Resize ortho indices to match HSI v1 shape
    fixed = {}
    for k, v in ortho.items():
        if v.shape != (H, W):
            sy = min(v.shape[0], H); sx = min(v.shape[1], W)
            new = np.full((H, W), np.nan, dtype=v.dtype)
            new[:sy, :sx] = v[:sy, :sx]
            fixed[k] = new
        else:
            fixed[k] = v

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Save 3-band raster
    band_arr = np.stack([fixed["ndvi"], fixed["ndmi"], fixed["ndii"]], axis=0)
    ba = xr.DataArray(band_arr, dims=("band", "y", "x"),
                      coords={"band": ["ndvi", "ndmi", "ndii"], "y": da_ref.y, "x": da_ref.x})
    ba.rio.write_crs(da_ref.rio.crs, inplace=True)
    out_tif = OUT_DIR / f"{site}_baselines.tif"
    ba.rio.to_raster(out_tif, compress="LZW", tiled=True)
    print(f"  saved -> {out_tif}")

    peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
    hsi_v1_arr = da_ref.values

    # Try BOTH directions for each baseline; pick the higher AUC.
    # In Korean pine winter scenes, raw NDVI (high = pine = burns) is often the
    # right direction, while typical "high stress = high index" intuition fails.
    results = {}
    for name in ("NDVI", "NDMI", "NDII"):
        raw = fixed[name.lower()]
        m = np.isfinite(raw)
        plo, phi = np.nanpercentile(raw[m], [5, 95])
        norm_raw = np.clip((raw - plo) / max(phi - plo, 1e-9), 0, 1)
        norm_inv = 1.0 - norm_raw

        r_raw = evaluate_burn(norm_raw, None, None, peri_path, da_ref)
        r_inv = evaluate_burn(norm_inv, None, None, peri_path, da_ref)
        if r_raw and r_inv:
            best = r_raw if r_raw["auc"] >= r_inv["auc"] else r_inv
            best["direction"] = "raw" if best is r_raw else "inv"
            results[name] = best
            print(f"  {name:>4} raw AUC={r_raw['auc']:.3f}  inv AUC={r_inv['auc']:.3f}  → {best['direction']} {best['auc']:.3f}  lift={best['lift']:.2f}x")

    r_v1 = evaluate_burn(hsi_v1_arr, None, None, peri_path, da_ref)
    if r_v1:
        results["HSI_v1"] = r_v1
        print(f"  HSI_v1     AUC={r_v1['auc']:.3f}  lift={r_v1['lift']:.2f}x")

    # 4-curve ROC overlay
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax = axes[0]
    colors = {"NDVI": "#fc8d59", "NDMI": "#74add1", "NDII": "#984ea3", "HSI_v1": "#a50026"}
    for name, r in results.items():
        ax.plot(r["fpr"], r["tpr"], color=colors.get(name, "k"), label=f"{name}  AUC={r['auc']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("ROC: HSI v1 vs spectral baselines (inverted)")
    ax.legend(loc="lower right")

    ax = axes[1]
    names = list(results.keys())
    aucs = [results[n]["auc"] for n in names]
    bars = ax.bar(names, aucs, color=[colors.get(n, "k") for n in names], alpha=0.85)
    ax.axhline(0.5, color="grey", linestyle="--")
    ax.set_ylabel("ROC AUC")
    ax.set_title(f"AUC comparison ({site})")
    ax.set_ylim(0.3, 0.85)
    for b, a in zip(bars, aucs):
        ax.text(b.get_x() + b.get_width()/2, a + 0.005, f"{a:.3f}", ha="center", fontsize=9)

    fig.suptitle(f"PineSentry-Fire {site.title()} — A5 ablation: HSI v1 vs spectral baselines", fontsize=12, y=1.02)
    fig.tight_layout()
    out_png = OUT_DIR / f"{site}_baselines_roc.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved -> {out_png}")

    # Save JSON summary (without numpy arrays)
    json_summary = {n: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items() if k not in ("fpr", "tpr")}
                    for n, r in results.items()}
    (OUT_DIR / f"{site}_summary.json").write_text(json.dumps(json_summary, indent=2))
    return json_summary


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for site in ("uiseong", "sancheong"):
        s = run_site(site)
        if s:
            summary[site] = s
    (OUT_DIR / "_overall.json").write_text(json.dumps(summary, indent=2))
    print(f"\n=== Overall ===")
    for site, s in summary.items():
        print(f"  {site}: " + ", ".join(f"{n}={r['auc']:.3f}" for n, r in s.items()))


if __name__ == "__main__":
    main()
