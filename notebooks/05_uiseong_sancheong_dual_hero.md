# Notebook 05 — Korean Dual Hero (의성 + 산청 2025-03)

> Week 8–9. **★ Hero figure 1차 산출물 ★** — 모든 노력의 수렴점.

## Cells

### Cell 1 — Load EMIT pre-fire granules (pre-registered IDs)

```python
import earthaccess, xarray as xr
earthaccess.login()

uiseong_baseline = earthaccess.search_data(
    short_name="EMITL2ARFL",
    granule_name="EMIT_L2A_RFL_001_20240216T044207_2404703_007"
)
sancheong_recent = earthaccess.search_data(
    short_name="EMITL2ARFL",
    granule_name="EMIT_L2A_RFL_001_20241219T032003_2435402_004"
)
# ... rest of pre-registered granule IDs
```

### Cell 2 — Apply Tanager-trained engine via EMIT cross-sensor

```python
from pinesentry_fire.traits import retrieve_traits
uiseong_traits = retrieve_traits(uiseong_refl, uiseong_wl, sensor="emit")
sancheong_traits = retrieve_traits(sancheong_refl, sancheong_wl, sensor="emit")
```

### Cell 3 — HSI computation (locked pre-registered weights)

```python
from pinesentry_fire.hsi import hydraulic_stress_index
uiseong_hsi = hydraulic_stress_index(uiseong_traits.lma_g_m2, uiseong_traits.ewt_mm)
sancheong_hsi = hydraulic_stress_index(sancheong_traits.lma_g_m2, sancheong_traits.ewt_mm)
```

### Cell 4 — Load 산림청 GIS perimeters

```python
import geopandas as gpd
uiseong_peri = gpd.read_file("data/fire_perimeter/uiseong2025.shp")
sancheong_peri = gpd.read_file("data/fire_perimeter/sancheong2025.shp")
```

### Cell 5 — Spatial logistic GLMM (forest-type stratified)

```python
# Filter to pine-only pixels (산림청 임상도 코드 31, 41 등)
# Spatial block CV with 1km blocks, seed=42
# Spatial GLMM via R-INLA / rpy2
```

### Cell 6 — Baseline comparison (5종 동시)

```python
# DWI (산림청 daily weather index)
# FWI (ECMWF)
# KBDI (Keetch-Byram drought)
# NDMI (Sentinel-2)
# NDVI difference (Sentinel-2)
# All evaluated on same Korean Hero pixels
```

### Cell 7 — ★ Hero figure 4-panel ★

```python
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(16, 9))
# A: Uiseong pre-fire HSI map + perimeter overlay
# B: Sancheong pre-fire HSI map + perimeter overlay
# C: Lift chart (Hero core) — both Uiseong + Sancheong overlaid
# D: ROC + PR (HSI vs DWI/FWI/NDMI/NDVI baselines)
fig.savefig("../figures/F5_hero_dual.png", dpi=300, bbox_inches="tight")
fig.savefig("../figures/F5_hero_dual.svg")  # for Figma polish
```

### Cell 8 — Statistical report

```python
# Print: HSI odds ratio (top vs bottom tertile), 95% CI
#        ROC-AUC, PR-AUC, Brier score, Boyce index
#        Permutation p-value (1000 shuffles)
#        ΔAUC vs each baseline
```

---

## Decision criteria (pre-registered)

H3 confirmed if:
- Odds ratio (top vs bottom HSI tertile) ≥ 1.5 with 95% CI > 1
- HSI ROC-AUC > best baseline by ≥ 0.05

If criteria fail: report transparent negative result (do not retune weights).

---

## Output

- `figures/F5_hero_dual.png` (1920×1080)
- `figures/F5_hero_dual.svg` (Figma source)
- `results/dual_hero_stats.json`
