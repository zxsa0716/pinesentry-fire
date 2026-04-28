"""Build first HSI map (v0) for Uiseong baseline EMIT scene + Hero figure draft.

This is a v0 pragmatic pipeline:
  1. Open EMIT L2A_RFL netCDF (already at-surface reflectance)
  2. Read sensor_band_parameters/wavelengths and pull NIR / SWIR1 / red bands
  3. Compute empirical proxies:
       NDVI         = (NIR858  - Red660 ) / (NIR858  + Red660 )
       NDII         = (NIR858  - SWIR1640) / (NIR858  + SWIR1640)   (moisture)
       NDWI_McFeet  = (Green560- NIR858 ) / (Green560+ NIR858 )     (water mask)
  4. EWT (mm) ≈ 0.30 + 0.20 * NDII             (empirical, Yebra 2013-ish)
     LMA (g/m²) ≈ 60 + 100 * NDVI              (placeholder, NDVI-LMA proxy)
  5. Ortho via the EMIT GLT lookup table on the location group.
  6. P50 species map: rasterize 의성 임상도 polygons → KOFTR_GROU_CD →
     species P50 (소나무 11→-3.0, 잣 12→-2.8, 신갈 32→-2.5, 굴참 33→-2.4,
     상수리 31→-2.5, 기타참 34→-2.5, 기타 →-2.7)
  7. HSI = 0.5*(1-HSM_norm) + 0.3*(1-EWT_norm) + 0.2*LMA_norm
     where HSM = psi_min - p50, psi_min = -0.3/EWT - 1.5
  8. Save:
       data/hsi/v0/uiseong_hsi_v0.tif
       data/hsi/v0/uiseong_hero_v0.png

Caveats: pre-trained PROSPECT inversion + ISOFIT atm correction are
deferred to v1. EMIT L2A is already at-surface, so the v0 atm step
is a no-op. v1 will replace empirical proxies with PROSPECT-D inversion.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import xarray as xr

warnings.filterwarnings("ignore")


EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")  # memory-verified, T-13mo, cc=21%, covers fire
IMSANGDO = Path("data/imsangdo/uiseong.gpkg")
OUT_DIR = Path("data/hsi/v0")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Species P50 (MPa) from TRY DB / lit consensus, keyed by both KOFTR code and Korean name.
# Imsangdo clip currently exposes KOFTR_NM (한글명) only — code column dropped.
P50_BY_KOFTR_CODE = {
    "11": -3.0,  # 소나무
    "12": -2.8,  # 잣나무
    "13": -2.4,  # 낙엽송
    "14": -3.5,  # 리기다소나무
    "15": -3.0,  # 곰솔
    "16": -3.0,  # 잔나무
    "17": -3.2,  # 편백나무
    "18": -2.8,  # 삼나무
    "31": -2.5,  # 상수리
    "32": -2.5,  # 신갈
    "33": -2.4,  # 굴참
    "34": -2.5,  # 기타참나무
    "35": -1.5,  # 오리나무 (riparian)
    "37": -1.8,  # 자작나무
    "39": -2.2,  # 밤나무
    "44": -2.0,  # 백합
    "47": -2.0,  # 느티
    "49": -2.0,  # 아까시
    "10": -2.7,  # 기타침엽수
    "30": -2.3,  # 기타활엽수
}
P50_BY_KOFTR_NM = {
    # Coniferous
    "소나무": -3.0,
    "잣나무": -2.8,
    "낙엽송": -2.4,
    "리기다소나무": -3.5,
    "곰솔": -3.0,
    "잔나무": -3.0,
    "전나무": -3.0,
    "편백나무": -3.2,
    "삼나무": -2.8,
    "비자나무": -2.5,
    "은행나무": -2.0,
    "기타침엽수": -2.7,
    # Broadleaf — Quercus group (drought-resistant)
    "신갈나무": -2.5,
    "굴참나무": -2.4,
    "상수리나무": -2.5,
    "갈참나무": -2.5,
    "졸참나무": -2.5,
    "기타 참나무류": -2.5,
    "기타참나무류": -2.5,
    # Other broadleaf
    "오리나무": -1.5,
    "자작나무": -1.8,
    "박달나무": -2.0,
    "밤나무": -2.2,
    "물푸레나무": -2.0,
    "서어나무": -2.0,
    "느티나무": -2.0,
    "벚나무": -1.8,
    "포플러": -1.5,
    "백합나무": -2.0,
    "아까시나무": -2.0,
    "고로쇠나무": -1.8,
    "기타활엽수": -2.3,
    # Mixed / bamboo
    "침활혼효림": -2.5,
    "죽림": -2.0,
    # Non-forest (excluded)
    "비산림": float("nan"),
    "미립목지": float("nan"),
    "관목덤불": float("nan"),
    "주거지": float("nan"),
    "초지": float("nan"),
    "경작지": float("nan"),
    "수체": float("nan"),
    "과수원": float("nan"),
    "기타": float("nan"),
}
P50_DEFAULT = -2.7


def open_emit(path: Path):
    """Open EMIT L2A RFL with sensor band wavelengths."""
    print(f"Opening {path.name} ...")
    rfl = xr.open_dataset(path, engine="h5netcdf")          # downtrack x crosstrack x bands
    bp = xr.open_dataset(path, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(path, engine="h5netcdf", group="location")
    return rfl, bp, loc


def nearest_band_idx(wavelengths: np.ndarray, target_nm: float) -> int:
    return int(np.argmin(np.abs(wavelengths - target_nm)))


def compute_indices(rfl_arr: np.ndarray, wls: np.ndarray) -> dict[str, np.ndarray]:
    """Return dict of NDVI, NDII, NDWI for the (downtrack, crosstrack) grid.

    rfl_arr shape: (downtrack, crosstrack, bands)
    """
    ib = {
        "blue":  nearest_band_idx(wls, 490),
        "green": nearest_band_idx(wls, 560),
        "red":   nearest_band_idx(wls, 660),
        "nir":   nearest_band_idx(wls, 858),
        "swir1": nearest_band_idx(wls, 1640),
        "swir2": nearest_band_idx(wls, 2200),
    }
    print(f"  band indices: {ib}")
    print(f"  nearest wavelengths (nm): " + ", ".join(f"{k}={wls[v]:.1f}" for k, v in ib.items()))

    R_red = rfl_arr[..., ib["red"]]
    R_nir = rfl_arr[..., ib["nir"]]
    R_swir1 = rfl_arr[..., ib["swir1"]]
    R_green = rfl_arr[..., ib["green"]]

    eps = 1e-6
    ndvi = (R_nir - R_red) / (R_nir + R_red + eps)
    ndii = (R_nir - R_swir1) / (R_nir + R_swir1 + eps)
    ndwi = (R_green - R_nir) / (R_green + R_nir + eps)
    return {"ndvi": ndvi, "ndii": ndii, "ndwi": ndwi, "ib": ib}


def empirical_traits(idx: dict) -> dict[str, np.ndarray]:
    """v0 empirical proxies (replace with PROSPECT-D inversion in v1)."""
    ndvi = idx["ndvi"]
    ndii = idx["ndii"]
    ewt = (0.30 + 0.20 * ndii).clip(0.05, 0.5)         # mm
    lma = (60 + 100 * np.clip(ndvi, 0, 1))             # g/m²
    return {"ewt": ewt, "lma": lma}


def orthorectify_via_glt(swath: np.ndarray, glt_x: np.ndarray, glt_y: np.ndarray, fill=np.nan):
    """Use EMIT GLT (geometric lookup table) to project swath array to ortho grid.

    glt_x[ortho_y, ortho_x] = crosstrack index (1-based; 0 = nodata)
    glt_y[ortho_y, ortho_x] = downtrack index  (1-based; 0 = nodata)
    """
    ortho = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    ortho[valid] = swath[yy, xx]
    return ortho


def hsm_to_hsi(ewt_o: np.ndarray, lma_o: np.ndarray, p50_o: np.ndarray):
    """Apply HSI formula on ortho arrays. NaN-safe."""
    eps = 1e-6
    ewt_safe = np.where(np.isnan(ewt_o) | (ewt_o <= 0.05), 0.05, ewt_o)
    psi_min = -0.3 / ewt_safe - 1.5                    # MPa
    hsm = psi_min - p50_o                              # +ve = safe (Martin-StPaul)

    def percentile_norm(a, lo=5, hi=95):
        m = np.isfinite(a)
        if m.sum() < 10:
            return np.zeros_like(a)
        plo, phi = np.nanpercentile(a[m], [lo, hi])
        if phi <= plo:
            return np.zeros_like(a)
        out = (a - plo) / (phi - plo)
        return np.clip(out, 0, 1)

    hsm_n = percentile_norm(hsm)
    ewt_n = percentile_norm(ewt_o)
    lma_n = percentile_norm(lma_o)
    hsi = 0.5 * (1 - hsm_n) + 0.3 * (1 - ewt_n) + 0.2 * lma_n
    return hsi, hsm, psi_min


def rasterize_p50(imsangdo_path: Path, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Build a P50 raster aligned to the EMIT ortho grid by per-pixel point-in-polygon
    lookup of imsangdo KOFTR_GROU_CD."""
    import geopandas as gpd

    print(f"Loading imsangdo polygons {imsangdo_path.name} ...")
    gdf = gpd.read_file(imsangdo_path)

    # Pre-pick the lookup column. Imsangdo SHP/GPKG variants:
    #   - KOFTR_GROU (10-char short, code in source FGDB)
    #   - KOFTR_GROU_CD (full standard)
    #   - KOFTR_NM (Korean name) — what our current 8-ROI clip exposes
    code_col = next((c for c in ("KOFTR_GROU_CD", "KOFTR_GROU") if c in gdf.columns), None)
    name_col = next((c for c in ("KOFTR_NM",) if c in gdf.columns), None)
    print(f"  available columns: {[c for c in gdf.columns if 'KOFTR' in c.upper()]}")

    if code_col is not None:
        gdf["_p50"] = gdf[code_col].astype(str).map(P50_BY_KOFTR_CODE).fillna(P50_DEFAULT)
        print(f"  P50 lookup via code column '{code_col}'")
    elif name_col is not None:
        gdf["_p50"] = gdf[name_col].astype(str).str.strip().map(P50_BY_KOFTR_NM).fillna(P50_DEFAULT)
        names = gdf[name_col].astype(str).str.strip().value_counts()
        unmatched = [n for n in names.index if n not in P50_BY_KOFTR_NM]
        if unmatched:
            print(f"  unmatched species names (default P50 applied): {unmatched[:10]}")
        print(f"  P50 lookup via name column '{name_col}'")
    else:
        print(f"  no KOFTR column — DEFAULT P50 everywhere")
        return np.full(lat.shape, P50_DEFAULT, dtype="float32")

    print(f"  P50 polygon distribution: " + " ".join(f"p{p}={np.percentile(gdf['_p50'].dropna(), p):.2f}" for p in [5, 50, 95]))

    # Rasterize the polygons onto the EMIT ortho grid using the bbox grid affine.
    # Build a regular ortho grid CRS=EPSG:4326 from the lat/lon arrays.
    valid = np.isfinite(lat) & np.isfinite(lon)
    if valid.sum() < 100:
        print(f"  not enough valid ortho pixels — DEFAULT")
        return np.full(lat.shape, P50_DEFAULT, dtype="float32")

    lons_1d = np.nanmean(lon, axis=0)
    lats_1d = np.nanmean(lat, axis=1)
    H, W = lat.shape
    res_x = abs(np.nanmedian(np.diff(lons_1d)))
    res_y = abs(np.nanmedian(np.diff(lats_1d)))
    x_min = np.nanmin(lons_1d)
    y_max = np.nanmax(lats_1d)

    from rasterio.transform import from_origin
    from rasterio.features import rasterize

    transform = from_origin(x_min, y_max, res_x, res_y)
    gdf_wgs = gdf.to_crs("EPSG:4326")
    shapes = ((geom, val) for geom, val in zip(gdf_wgs.geometry, gdf_wgs["_p50"]) if geom and not np.isnan(val))
    p50 = rasterize(
        shapes=shapes,
        out_shape=(H, W),
        transform=transform,
        fill=P50_DEFAULT,
        dtype="float32",
    )
    return p50


def render_hero_png(out_png: Path, hsi: np.ndarray, lat: np.ndarray, lon: np.ndarray, perimeter_path: Path | None):
    """v0 Hero figure: 1x2 panel — full-scene HSI + zoomed-in HSI w/ perimeter overlay."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("hsi", ["#1a9850", "#fee08b", "#f46d43", "#a50026"])
    extent = [np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)]

    peri = None
    peri_bounds = None
    if perimeter_path and perimeter_path.exists():
        try:
            import geopandas as gpd
            peri = gpd.read_file(perimeter_path).to_crs("EPSG:4326")
            peri_bounds = peri.total_bounds  # (minx, miny, maxx, maxy)
            print(f"  overlay: {perimeter_path.name} ({len(peri)} perimeters)")
            print(f"  perimeter bounds: {peri_bounds}")
        except Exception as e:
            print(f"  overlay load failed: {e}")

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Left: full scene
    ax = axes[0]
    im = ax.imshow(hsi, origin="upper", cmap=cmap, extent=extent, vmin=0, vmax=1)
    if peri is not None:
        peri.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=1.5)
    ax.set_title(f"Full EMIT scene ({EMIT_NC.name.split('_')[4][:8]} pre-fire baseline)")
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")

    # Right: zoom on fire area (perimeter ± 0.05°)
    ax = axes[1]
    im2 = ax.imshow(hsi, origin="upper", cmap=cmap, extent=extent, vmin=0, vmax=1)
    if peri is not None:
        peri.plot(ax=ax, facecolor="red", edgecolor="darkred", linewidth=0.5, alpha=0.4)
        peri.boundary.plot(ax=ax, edgecolor="darkred", linewidth=2.0)
        pad = 0.05
        ax.set_xlim(peri_bounds[0] - pad, peri_bounds[2] + pad)
        ax.set_ylim(peri_bounds[1] - pad, peri_bounds[3] + pad)
    ax.set_title("Zoom: dNBR-derived 2025-03-22 burn perimeter (red)")
    ax.set_xlabel("Longitude (°E)")

    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cb.set_label("Hydraulic Stress Index v0  (0 = safe, 1 = stressed)")
    fig.suptitle("PineSentry-Fire v0 — Uiseong  |  EMIT pre-fire HSI (5 nm SWIR) vs S2 dNBR burn perimeter", fontsize=13, y=1.02)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Hero PNG -> {out_png}")


def main():
    if not EMIT_NC.exists():
        print(f"Missing EMIT scene: {EMIT_NC}", file=sys.stderr)
        sys.exit(1)

    rfl_ds, bp_ds, loc_ds = open_emit(EMIT_NC)
    print(f"  reflectance dims: {rfl_ds.reflectance.dims} shape: {rfl_ds.reflectance.shape}")
    print(f"  ortho_y x ortho_x: {loc_ds.glt_x.shape}")

    wls = bp_ds.wavelengths.values
    print(f"  bands: {len(wls)}, range {wls.min():.1f}-{wls.max():.1f} nm")

    rfl_arr = rfl_ds.reflectance.values        # (downtrack, crosstrack, bands)
    print(f"  reflectance loaded: shape={rfl_arr.shape}, dtype={rfl_arr.dtype}")
    rfl_arr = np.where(rfl_arr < -1, np.nan, rfl_arr)

    idx = compute_indices(rfl_arr, wls)
    traits = empirical_traits(idx)
    print(f"  EWT range: {np.nanpercentile(traits['ewt'], [5, 50, 95])}")
    print(f"  LMA range: {np.nanpercentile(traits['lma'], [5, 50, 95])}")

    # Ortho via GLT
    glt_x = loc_ds.glt_x.values
    glt_y = loc_ds.glt_y.values
    lon_o = orthorectify_via_glt(loc_ds.lon.values, glt_x, glt_y)
    lat_o = orthorectify_via_glt(loc_ds.lat.values, glt_x, glt_y)
    ewt_o = orthorectify_via_glt(traits["ewt"], glt_x, glt_y)
    lma_o = orthorectify_via_glt(traits["lma"], glt_x, glt_y)
    ndvi_o = orthorectify_via_glt(idx["ndvi"], glt_x, glt_y)
    ndii_o = orthorectify_via_glt(idx["ndii"], glt_x, glt_y)
    print(f"  ortho grid: {lon_o.shape}")

    p50_o = rasterize_p50(IMSANGDO, lat_o, lon_o)
    print(f"  P50 grid stats: min={np.nanmin(p50_o):.2f} median={np.nanmedian(p50_o):.2f} max={np.nanmax(p50_o):.2f}")

    hsi, hsm, psi = hsm_to_hsi(ewt_o, lma_o, p50_o)
    print(f"  HSI distribution: " + " ".join(f"p{p}={np.nanpercentile(hsi, p):.2f}" for p in [5, 25, 50, 75, 95]))

    # Save GeoTIFF
    import rioxarray as rxr
    da = xr.DataArray(
        hsi, dims=("y", "x"),
        coords={
            "lat": (("y", "x"), lat_o),
            "lon": (("y", "x"), lon_o),
        },
        name="hsi_v0",
    )
    da.attrs.update({
        "long_name": "Hydraulic Stress Index v0 (Tanager-aligned EMIT)",
        "version": "v0",
        "weights_safety_water_starch": "0.5,0.3,0.2",
        "trait_proxies": "EWT=NDII-empirical; LMA=NDVI-empirical",
        "p50_source": "imsangdo KOFTR_GROU + literature mean",
        "scene": EMIT_NC.name,
    })

    # Build a 1D-coord proxy for GeoTIFF (use mean of each row/col in the ortho grid)
    # since the EMIT GLT grid is regular in projected EPSG:4326 by construction
    lons_1d = np.nanmean(lon_o, axis=0)
    lats_1d = np.nanmean(lat_o, axis=1)
    da2 = xr.DataArray(hsi, dims=("y", "x"), coords={"y": lats_1d, "x": lons_1d}, name="hsi_v0")
    da2.attrs = da.attrs
    da2.rio.write_crs("EPSG:4326", inplace=True)
    out_tif = OUT_DIR / "uiseong_hsi_v0.tif"
    da2.rio.to_raster(out_tif, compress="LZW", tiled=True)
    print(f"  GeoTIFF -> {out_tif} ({out_tif.stat().st_size/1e6:.1f} MB)")

    # Hero PNG
    out_png = OUT_DIR / "uiseong_hero_v0.png"
    perimeter = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
    render_hero_png(out_png, hsi, lat_o, lon_o, perimeter)


if __name__ == "__main__":
    main()
