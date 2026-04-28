# Notebook 02 — ISOFIT Atmospheric Correction

> Week 1–2. ISOFIT (https://github.com/isofit/isofit) is JPL's gold-standard
> atm-corr for hyperspectral. EMIT L2A ships pre-corrected; Tanager L1B
> requires ISOFIT.

## Cells

### Cell 1 — ISOFIT install (Docker recommended)

```bash
docker pull isofit/isofit:latest
docker run --rm -v $(pwd)/data:/data isofit/isofit isofit --help
```

### Cell 2 — Tanager L1B → BOA reflectance (5 scenes)

```python
# Wraps ISOFIT subcommand for each Tanager Basic Radiance HDF5
from pinesentry_fire.isofit_pipeline import isofit_correct
for scene_id in tanager_scenes:
    isofit_correct(scene_id, output_dir="data/tanager_l2a/")
```

### Cell 3 — EMIT L2A direct read (already corrected)

```python
import xarray as xr
ds_uiseong = xr.open_dataset("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
```

### Cell 4 — Sentinel-2 L2A direct (Sen2Cor BOA)

```python
# AWS Open Data 직접 읽기 (rioxarray)
```

### Cell 5 — Wavelength registration (5 nm 공통 격자)

```python
from pinesentry_fire.wavelength_register import to_common_grid
ds_unified = to_common_grid([tanager_ds, emit_ds, hyperion_ds], target_grid_nm=np.arange(380, 2500, 5))
```

### Fallback if ISOFIT 막힘

- 6SV vector 사용 (lighter)
- Planet L2A direct (Open Data Catalog가 점진적 제공)

---

## Output

- `data/tanager_l2a/*.nc` — surface reflectance
- `data/unified/*.nc` — wavelength-aligned cubes
