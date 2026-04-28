# Notebook 04 — US Validation (LA Palisades 2025-01)

> Week 7. Pre-fire window: Tanager 2024-08 ~ 2025-01-06 (5 months).
> Validates the engine in-domain (Tanager native) before EMIT cross-sensor transfer.

## Cells

### Cell 1 — Load Palisades pre-fire Tanager scenes

```python
from pystac_client import Client
c = Client.open("https://www.planet.com/data/stac/browser/tanager-core-imagery/catalog.json")
items = c.search(bbox=[-118.58, 34.03, -118.49, 34.10],
                 datetime="2024-08-01/2025-01-06").item_collection()
```

### Cell 2 — Run engine → 5-channel trait map

```python
from pinesentry_fire.traits import retrieve_traits
result = retrieve_traits(palisades_refl, palisades_wl, sensor="tanager")
```

### Cell 3 — HSI computation (pre-registered weights)

```python
from pinesentry_fire.hsi import hydraulic_stress_index
hsi = hydraulic_stress_index(result.lma_g_m2, result.ewt_mm, species_map=None)
```

### Cell 4 — MTBS Palisades perimeter overlay

```python
import geopandas as gpd
peri = gpd.read_file("data/mtbs/pinesentry_us_targets.gpkg")
palisades = peri[peri.Incid_Name.str.contains("PALISADES")].iloc[0].geometry
```

### Cell 5 — Spatial logistic GLMM (R-INLA via rpy2)

```python
# rpy2 → R-INLA spatial regression
# Or use pymc4 / numpyro spatial Gaussian Process
```

### Cell 6 — Lift chart + ROC curves

```python
# C: lift chart (HSI decile vs burn fraction with 95% CI)
# D: ROC HSI vs KBDI/NDVI baselines + AUC
```

### Cell 7 — Save Palisades figure

```python
fig.savefig("../figures/F4_palisades_us_validation.png", dpi=300)
```

---

## Decision criteria (pre-registered)

- Pass: AUC ≥ 0.65 + lift (top decile) ≥ 1.5x
- Fail: report negative result and proceed cautiously to Korean validation
