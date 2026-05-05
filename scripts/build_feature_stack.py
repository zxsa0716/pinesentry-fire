"""Build per-pixel multi-layer feature stack for v1 HSI.

Inputs (already on disk):
  data/hsi/v0/uiseong_hsi_v0.tif         — empirical HSI proxy (EWT/LMA/NDII)
  data/hsi/v0/uiseong_firerisk_v0.tif    — 1 - HSI v0 (the AUC=0.697 scorer)
  data/dem/copdem30_{roi}.tif            — elevation
  data/imsangdo/{roi}.gpkg               — species + age + density polygons
  data/worldcover/worldcover_{roi}.tif   — ESA 10m land cover class

Outputs:
  data/features/{roi}_stack.tif          — multi-band GeoTIFF aligned to HSI grid
    band 1: hsi_v0_safety
    band 2: firerisk_v0       (= 1 - hsi_v0_safety)
    band 3: elev_m
    band 4: slope_deg
    band 5: aspect_deg        (0=N, 90=E, 180=S, 270=W)
    band 6: south_facing      (cos(aspect-180)+1)/2 in [0,1]
    band 7: pyrophilic_factor (0..1, species-specific)
    band 8: pine_fraction     (1 if species in Pinus group else 0)
    band 9: worldcover_class  (10 tree, 20 shrub, 30 grass, 40 crop, 50 built, ...)
    band 10: pine_terrain     pyrophilic * south_facing — combined v0.7 score
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr
import xarray as xr

ROI = sys.argv[1] if len(sys.argv) > 1 else "uiseong"
HSI_TIF = Path(f"data/hsi/v0/{ROI}_hsi_v0.tif")
FIRERISK_TIF = Path(f"data/hsi/v0/{ROI}_firerisk_v0.tif")
DEM_TIF = Path(f"data/dem/copdem30_{ROI}.tif")
IMSANGDO = Path(f"data/imsangdo/{ROI}.gpkg")
WORLDCOVER_TIF = Path(f"data/worldcover/worldcover_{ROI}.tif")
OUT = Path(f"data/features/{ROI}_stack.tif")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Pyrophilic factor by Korean species name. High = pine/conifer (resin, low P50);
# Low = mesic broadleaf.
PYROPHILIC = {
    # Pyrophilic conifers
    "Pinus densiflora (Korean red pine)": 1.00,
    "Pinus koraiensis": 0.85,
    "Larix": 0.55,
    "Pinus rigidaPinus densiflora (Korean red pine)": 0.95,
    "Pinus thunbergii": 0.95,
    "Abies sp.": 0.70,
    "Picea sp.": 0.65,
    "Cupressus나무": 0.60,
    "Cryptomeria": 0.55,
    "Torreya나무": 0.50,
    "은행나무": 0.30,
    "기타침엽수": 0.65,
    # Drought-tolerant oaks (intermediate)
    "Quercus mongolica나무": 0.50,
    "Quercus variabilis나무": 0.55,
    "Quercus acutissima나무": 0.50,
    "갈참나무": 0.45,
    "졸참나무": 0.45,
    "기타 참나무류": 0.50,
    "기타참나무류": 0.50,
    # Mesic broadleaves (low pyrophilic)
    "오리나무": 0.20,
    "Betula나무": 0.25,
    "Betula schmidtii나무": 0.30,
    "Castanea나무": 0.30,
    "Fraxinus나무": 0.25,
    "Carpinus나무": 0.25,
    "Zelkova나무": 0.20,
    "Prunus나무": 0.25,
    "포플러": 0.20,
    "백합나무": 0.30,
    "Robinia pseudoacacia나무": 0.40,
    "고로쇠나무": 0.30,
    "기타활엽수": 0.40,
    # Mixed
    "침활mixed forest": 0.60,
    "bamboo": 0.30,
    # Non-forest
    "non-forest": 0.0,
    "미립목지": 0.0,
    "관목덤불": 0.20,
    "주거지": 0.0,
    "초지": 0.10,
    "경작지": 0.0,
    "수체": 0.0,
    "과수원": 0.0,
    "기타": 0.10,
    "제지": 0.0,
}
PINE_NAMES = {"Pinus densiflora (Korean red pine)", "Pinus koraiensis", "Pinus rigidaPinus densiflora (Korean red pine)", "Pinus thunbergii", "Abies sp.", "Picea sp.", "Cupressus나무", "Cryptomeria"}


def slope_aspect(dem: np.ndarray, res_m: float) -> tuple[np.ndarray, np.ndarray]:
    """Horn's algorithm — slope (deg) + aspect (deg, 0=N CW)."""
    dz_dx = np.zeros_like(dem)
    dz_dy = np.zeros_like(dem)
    dz_dx[:, 1:-1] = (dem[:, 2:] - dem[:, :-2]) / (2 * res_m)
    dz_dy[1:-1, :] = (dem[:-2, :] - dem[2:, :]) / (2 * res_m)
    slope_rad = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
    aspect_rad = np.arctan2(dz_dy, -dz_dx)
    aspect_deg = (90.0 - np.degrees(aspect_rad)) % 360.0
    return np.degrees(slope_rad).astype("float32"), aspect_deg.astype("float32")


def main():
    if not HSI_TIF.exists():
        print(f"Need HSI v0 first: {HSI_TIF}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading HSI v0 grid as reference: {HSI_TIF}")
    hsi = rxr.open_rasterio(HSI_TIF, masked=True).squeeze()
    fr = rxr.open_rasterio(FIRERISK_TIF, masked=True).squeeze()
    print(f"  HSI grid: {hsi.shape}, CRS={hsi.rio.crs}, bounds={hsi.rio.bounds()}")

    # ---- DEM: reproject + clip + slope/aspect ----
    print(f"Loading DEM: {DEM_TIF}")
    if DEM_TIF.exists():
        dem = rxr.open_rasterio(DEM_TIF, masked=True).squeeze()
        dem_match = dem.rio.reproject_match(hsi)
        dem_arr = dem_match.values.astype("float32")
        # Approx pixel size — convert hsi grid to meters (one degree ~ 111km, scale by lat)
        lat0 = float(hsi.y.mean())
        deg_to_m_x = 111000 * np.cos(np.deg2rad(lat0))
        deg_to_m_y = 111000
        res_y = abs(float(hsi.y[1] - hsi.y[0])) * deg_to_m_y
        res_x = abs(float(hsi.x[1] - hsi.x[0])) * deg_to_m_x
        res = (res_x + res_y) / 2
        print(f"  approx pixel size: {res:.1f} m")
        slope, aspect = slope_aspect(dem_arr, res)
        south_facing = (np.cos(np.deg2rad(aspect - 180)) + 1) / 2
    else:
        print(f"  DEM missing — zeros")
        dem_arr = np.zeros(hsi.shape, dtype="float32")
        slope = np.zeros_like(dem_arr)
        aspect = np.zeros_like(dem_arr)
        south_facing = np.zeros_like(dem_arr)

    # ---- Imsangdo: rasterize pyrophilic + pine fraction ----
    print(f"Loading imsangdo {IMSANGDO}")
    import geopandas as gpd
    from rasterio.features import rasterize
    gdf = gpd.read_file(IMSANGDO).to_crs("EPSG:4326")
    name_col = next((c for c in gdf.columns if "KOFTR" in c.upper() and "NM" in c.upper()), None)
    print(f"  species col: {name_col}")
    gdf["_pyrophilic"] = gdf[name_col].astype(str).str.strip().map(PYROPHILIC).fillna(0.30)
    gdf["_is_pine"] = gdf[name_col].astype(str).str.strip().isin(PINE_NAMES).astype("uint8")
    print(f"  pyrophilic distribution: " + " ".join(f"p{p}={np.percentile(gdf['_pyrophilic'].dropna(), p):.2f}" for p in [5, 50, 95]))
    print(f"  pine polygons: {gdf['_is_pine'].sum()} / {len(gdf)}")

    H, W = hsi.shape
    transform = hsi.rio.transform()
    pyro_arr = rasterize(
        ((g, v) for g, v in zip(gdf.geometry, gdf["_pyrophilic"]) if g and not np.isnan(v)),
        out_shape=(H, W), transform=transform, fill=0.30, dtype="float32",
    )
    pine_arr = rasterize(
        ((g, v) for g, v in zip(gdf.geometry, gdf["_is_pine"]) if g),
        out_shape=(H, W), transform=transform, fill=0, dtype="uint8",
    )

    # ---- WorldCover ----
    from rasterio.enums import Resampling
    if WORLDCOVER_TIF.exists():
        print(f"Loading WorldCover: {WORLDCOVER_TIF}")
        wc = rxr.open_rasterio(WORLDCOVER_TIF, masked=False).squeeze()
        wc_match = wc.rio.reproject_match(hsi, resampling=Resampling.nearest)
        wc_arr = wc_match.values.astype("uint8")
    else:
        print(f"  WorldCover missing — zeros")
        wc_arr = np.zeros(hsi.shape, dtype="uint8")

    # ---- Combined v0.7 score: pyrophilic * south_facing * (1 - HSI) ----
    pine_terrain = pyro_arr * south_facing

    # ---- Stack all bands ----
    target_shape = hsi.values.shape
    print(f"  target shape: {target_shape}")
    arrs = {
        "hsi_v0": hsi.values.astype("float32"),
        "firerisk_v0": fr.values.astype("float32"),
        "elev_m": dem_arr,
        "slope_deg": slope,
        "aspect_deg": aspect,
        "south_facing": south_facing.astype("float32"),
        "pyrophilic": pyro_arr.astype("float32"),
        "pine_fraction": pine_arr.astype("float32"),
        "worldcover": wc_arr.astype("float32"),
        "pine_terrain": pine_terrain.astype("float32"),
    }
    for k, v in arrs.items():
        if v.shape != target_shape:
            print(f"  shape mismatch {k}: {v.shape} -> resize to {target_shape}")
            # Crop or pad to match — simple strategy: take overlapping region
            sy = min(v.shape[0], target_shape[0])
            sx = min(v.shape[1], target_shape[1])
            new = np.zeros(target_shape, dtype=v.dtype)
            new[:sy, :sx] = v[:sy, :sx]
            arrs[k] = new
    stack = np.stack(list(arrs.values()), axis=0)
    band_names = ["hsi_v0", "firerisk_v0", "elev_m", "slope_deg", "aspect_deg",
                  "south_facing", "pyrophilic", "pine_fraction", "worldcover", "pine_terrain"]

    # Save
    da = xr.DataArray(stack, dims=("band", "y", "x"),
                      coords={"band": band_names, "y": hsi.y, "x": hsi.x})
    da.rio.write_crs(hsi.rio.crs, inplace=True)
    da.rio.to_raster(OUT, compress="LZW", tiled=True)
    print(f"\nSaved feature stack -> {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")
    print(f"  band names: {band_names}")
    print(f"  shape: {stack.shape}")


if __name__ == "__main__":
    main()
