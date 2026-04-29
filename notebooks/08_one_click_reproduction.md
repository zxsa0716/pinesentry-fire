# 08 — One-click PineSentry-Fire v1 reproduction

This notebook reproduces the v1 Uiseong + Sancheong AUC results from a
fresh Colab runtime in ~30-60 minutes (data download dominated).

## 0. Auth + install

```python
!pip install -q earthaccess pystac-client rioxarray geopandas h5netcdf scikit-learn

import earthaccess
auth = earthaccess.login(strategy="interactive")   # paste URS credentials
```

## 1. Clone + setup

```python
!git clone https://github.com/zxsa0716/pinesentry-fire.git
%cd pinesentry-fire
```

## 2. Download (20-30 min)

```python
!python scripts/download_emit_specific.py            # Uiseong T-13mo baseline
!python scripts/download_emit.py                      # auto-pick winter scenes
!python scripts/synth_perimeter_dnbr.py               # S2 dNBR for 4 fires
!python scripts/download_dem_copernicus.py            # COP-DEM 30m (12 ROIs)
!python scripts/clip_imsangdo.py                       # Korean Forest Service polygons (assumes user pre-downloaded gdb)
```

> **Note**: Korean 임상도 1:5,000 (~4 GB FGDB) requires data.go.kr login —
> place at `data/imsangdo/TB_FGDI_FS_IM5000.gdb/` before running clip_imsangdo.py.

## 3. Build v0 + v1 + eval (5 min)

```python
!python scripts/build_hsi_v0.py uiseong
!python scripts/evaluate_hsi_v0.py uiseong            # AUC = 0.697
!python scripts/build_feature_stack.py uiseong
!python scripts/build_hsi_v1.py uiseong               # AUC = 0.747

!python scripts/build_hsi_v0.py sancheong
!python scripts/evaluate_hsi_v0.py sancheong
!python scripts/build_feature_stack.py sancheong
!python scripts/build_hsi_v1.py sancheong             # AUC = 0.647
```

## 4. Compare against spectral baselines

```python
!python scripts/compute_spectral_baselines.py
!python scripts/make_final_hero.py
```

Expected outputs:

```
data/hsi/v0/uiseong_eval_v0.png
data/hsi/v0/sancheong_eval_v0.png
data/hsi/v1/uiseong_eval_v1.png
data/hsi/v1/sancheong_eval_v1.png
data/hsi/v1/HERO_final.png
data/baselines/uiseong_baselines_roc.png
data/baselines/sancheong_baselines_roc.png
```

## 5. Spatial-block CV

```python
!python scripts/spatial_block_cv.py uiseong 4
!python scripts/spatial_block_cv.py sancheong 4
```

Reports per-fold AUC mean/std confirming weights are robust to spatial folds.

## 6. Run tests

```python
!PYTHONPATH=src pytest tests/test_hsi.py -v
```

Should print `9 passed`.

## 7. Streamlit demo

```python
!streamlit run streamlit_app/app.py
```

Or push to HuggingFace Spaces (free):

```bash
huggingface-cli login
huggingface-cli repo create pinesentry-fire --type space --space_sdk streamlit
git remote add space https://huggingface.co/spaces/USERNAME/pinesentry-fire
git push space main
```
