# Notebook 06 — KoFlux 광릉 sanity check (carbon flux × HSI)

> Week 10. **AGU B (Biogeosciences) 청중 어필** — dual validation의 carbon side.

## Cells

### Cell 1 — Load KoFlux GDK NEE/GPP 18-month series

```python
import pandas as pd
gdk = pd.read_csv("data/koflux_gdk/gdk_30min_nee_gpp_2024_2026.csv")
gdk_daily = gdk.resample("D", on="time").mean()
```

### Cell 2 — Load EMIT 광릉 scenes (multiple snapshots)

```python
import earthaccess
emit_gwangneung = earthaccess.search_data(
    short_name="EMITL2ARFL",
    bounding_box=(127.10, 37.70, 127.20, 37.80),
    temporal=("2022-08-01", "2026-04-30"),
)
```

### Cell 3 — Apply engine + extract HSI for KoFlux footprint pixel

```python
from pinesentry_fire.traits import retrieve_traits
from pinesentry_fire.hsi import hydraulic_stress_index

hsi_series = []
for scene in emit_gwangneung:
    refl = ...  # load
    traits = retrieve_traits(refl, ..., sensor="emit")
    hsi = hydraulic_stress_index(traits.lma_g_m2, traits.ewt_mm)
    # Extract 1 pixel at 광릉 GDK tower coordinate (37.7493°N, 127.1486°E)
    hsi_series.append({"date": scene.date, "hsi": hsi.sel(...).item()})
```

### Cell 4 — NEE residual decomposition

```python
# NEE = NEE_climatology + NEE_residual
# NEE_climatology = monthly mean over 25-yr KoFlux record
# NEE_residual = current NEE - climatology
```

### Cell 5 — HSI × NEE residual correlation

```python
from scipy import stats
r, p = stats.pearsonr(hsi_aligned.values, nee_residual_aligned.values)
print(f"HSI × NEE residual: r = {r:.3f}, p = {p:.4f}")
```

### Cell 6 — F6 figure: time series overlay + scatter

```python
fig, axes = plt.subplots(2, 1, figsize=(10, 6))
# Top: time series HSI + NEE residual overlay (2024-08 ~ 2026-04)
# Bottom: scatter with regression
```

---

## Decision criteria

- Pre-registered: report Pearson r and p-value
- Expected: r > 0.4 indicates HSI captures stress-driven carbon flux variability
- If r < 0.2: HSI fails Tier-1 sanity → reframe as fire-only (drop NEE narrative)

## Output

- `figures/F6_koflux_check.png`
- `results/koflux_correlation.json`
