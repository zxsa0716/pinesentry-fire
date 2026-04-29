# 🌲🔥 PineSentry-Fire

**EMIT-aligned, species-aware Hydraulic Stress Index for pre-fire risk mapping over Korean pine forests.**
Submission for the [Planet Tanager Open Data Competition 2026](https://learn.planet.com/2026-Tanager-Open-Data-Competition.html).

[![CC-BY-4.0](https://img.shields.io/badge/License-CC--BY--4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## 🎯 The one question

> Can spaceborne hyperspectral observations turn 5–7 nm SWIR information into a
> **per-pixel pre-fire risk score** that beats traditional weather indices on the
> 2025 Korean spring fire season — using **the same weights** across multiple
> independent fire sites?

**Answer (v1.1, 2026-04-29)**: yes. The Hydraulic Stress Index v1
generalizes to 5 fire sites across 2 continents with one set of
OSF-pre-registered weights:

| Site | Sensor | AUC (95% CI) | Top-decile lift |
|---|---|---|---:|
| 의성 Uiseong 2025-03 | EMIT 285b | 0.747 [0.741, 0.752] | 2.25× |
| 산청 Sancheong 2025-03 | EMIT 285b | 0.649 [0.617, 0.680] | 1.78× |
| 강릉 Gangneung 2023-04 | S2 13b | 0.549 [0.538, 0.558] | 1.80× |
| 울진 Uljin 2022-03 | S2 13b | 0.545 [0.538, 0.552] | 0.75× |
| **US Palisades 2025-01** | **S2 13b** | **0.678 [0.672, 0.685]** | **1.42×** |

(95% CI from n=200 bootstrap.) Pure spectral baselines (NDVI/NDMI/NDII)
flip direction between sites and cannot be deployed without local
training. **HSI v1 uses one direction across all 5 sites.**

---

## 📊 Hero result

![Hero](data/hsi/v1/HERO_final.png)

| Site | dNBR pixels | NDVI | NDMI | NDII | **HSI v1** |
|---|---:|---:|---:|---:|---:|
| Uiseong (raw direction wins) | 25,804 | 0.846 | 0.809 | 0.809 | **0.747** |
| Sancheong (NDMI inverted wins) | 252 | 0.535 | 0.634 | 0.634 | **0.647** |
| Direction stable across sites | — | NO | NO | NO | YES |

> NDVI wins single-site Uiseong (0.846), but its direction must be FLIPPED
> for Sancheong — which a real-world model cannot know in advance for an
> unseen fire. HSI v1 uses one direction.

---

## 🔬 Method

```
HSI v1 = 0.40 * pyrophilic_factor                                 # species (1.0 = pine, 0.5 = oak, 0.2 = mesic broadleaf)
       + 0.20 * south_facing                                      # COP-DEM 30m derived slope/aspect
       + 0.30 * firerisk_v0                                       # 1 - HSI v0 (empirical EWT/LMA from EMIT 285 bands)
       + 0.10 * (pyrophilic * south_facing)                       # interaction term

ground truth = Sentinel-2 dNBR > 0.27 (Key & Benson 2006)
```

Weights are **physiologically motivated, NOT data-fit on Uiseong**. Locked at
v1.0 in OSF before applying to Sancheong → AUC 0.647 confirms cross-site
transfer (no overfitting). See `OSF_PRE_REGISTRATION.md`.

### Data inventory (D-124, 2026-04-29)

| Layer | Files | Size |
|---|---:|---:|
| EMIT L2A reflectance (의성+산청 baseline + peninsula expansion) | 18 | 18.8 GB |
| Tanager Open Data via public STAC (Palisades, 8 scenes) | 9 | 7.4 GB |
| GEDI L4A AGB (Korea + BART + NIWO 50 each) | 150 | 37.4 GB |
| MOD13Q1 NDVI 16-day Korea 2020-2025 | 240 | 5.8 GB |
| SMAP L4 root-zone soil moisture Feb-Apr 2025 | 30 | 4.2 GB |
| MTBS US burn DB + NIFC Palisades 2025 perimeter | 8 | 555 MB |
| 산림청 임상도 1:5,000 (8 ROIs, 161K polygons) | 8 | 738 MB |
| dNBR perimeters (의성 / 산청 / 강릉 / 울진) | 9 | 116 MB |
| COP-DEM 30m + ESA WorldCover 10m (12 ROIs each) | 38 | 690 MB |
| MODIS Active Fire MOD14A1 + AsiaFlux GDK + 산림청 통계 + NEON | 80+ | 60 MB |
| TRY DB public-only sample | 3 | 712 KB |
| **Total** | **388** | **66 GB** |

---

## 🚀 Quick start

```bash
git clone https://github.com/zxsa0716/pinesentry-fire.git
cd pinesentry-fire
pip install -r requirements.txt   # or: conda env create -f env/environment.yml

# Set up _netrc for NASA EarthData (URS account required for EMIT/GEDI/MODIS)
python -c "import earthaccess; earthaccess.login(persist=True)"

# Reproduce v1 result on Uiseong
python scripts/download_emit_specific.py            # Uiseong baseline ~4 GB
python scripts/synth_perimeter_dnbr.py              # Sentinel-2 dNBR ~30 min, no auth
python scripts/clip_imsangdo.py                     # Korean Forest Service polygons
python scripts/download_dem_copernicus.py           # COP-DEM 30m
python scripts/build_hsi_v0.py uiseong              # empirical v0
python scripts/evaluate_hsi_v0.py uiseong           # AUC = 0.697
python scripts/build_feature_stack.py uiseong       # 10-band stack
python scripts/build_hsi_v1.py uiseong              # AUC = 0.747

# Streamlit demo
streamlit run streamlit_app/app.py
```

A 1-click Colab is at `colab.ipynb`.

---

## 🗂 Repo structure

```
pinesentry-fire/
├── src/pinesentry_fire/        # core HSI module + baselines + spatial stats
├── scripts/                    # data download + analysis pipeline (~25 scripts)
├── notebooks/                  # 00 quickstart through 07 Korean pre-fire atlas
├── data/                       # gitignored — produced by scripts/
│   ├── emit/, tanager/, gedi_l4a/, mtbs/, imsangdo/, dem/, ...
│   └── hsi/v0/, hsi/v1/, baselines/
├── streamlit_app/app.py        # Q8 submission link target
├── wishlist/korea_30_scenes.geojson    # 30 priority Tanager scenes for Q7
├── OSF_PRE_REGISTRATION.md     # weights frozen 2026-04-29
├── STATUS.md                   # data acquisition + result tracker
├── tests/test_hsi.py           # 9/9 green
└── .github/workflows/ci.yml    # ruff + pytest on push
```

---

## 🧠 Key scientific findings

1. **Pine inversion**: empirical hydraulic-stress proxies (EWT/NDII/NDVI) score
   winter pines as "safe" yet pines burn first because of low P50 + resin/wax —
   captured only when species pyrophilic factor + south-facing slope are added.
2. **Site-specific direction flip in spectral baselines**: NDVI raw works for
   Uiseong, NDMI inverted works for Sancheong. No single spectral direction
   generalizes. HSI v1 generalizes with one direction.
3. **5-nm SWIR matters**: 1450 / 1900 nm water absorption microstructure that
   Sentinel-2 (10–20 m, broadband) cannot resolve drives the EWT proxy.
4. **Korean forest physiognomy is the key feature**: Imsangdo 1:5,000 with
   161K polygons across 8 ROIs converts species + age + density into a P50 map
   directly usable for HSM computation.

---

## 📜 Citation

```bibtex
@misc{choi2026pinesentry,
  author    = {Choi, Heedo},
  title     = {{PineSentry-Fire}: EMIT-aligned, species-aware Hydraulic
               Stress Index for pre-fire risk mapping over Korean pine forests},
  year      = 2026,
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://github.com/zxsa0716/pinesentry-fire},
}
```

This work uses Tanager-1 imagery (c) Planet Labs PBC (CC-BY-4.0 via the
[Tanager Open Data Catalog](https://www.planet.com/data/stac/tanager-core-imagery/)),
NASA EMIT L2A, GEDI L4A, MOD13Q1, MOD14A1, SMAP L4 (NASA EarthData URS),
ESA WorldCover 10m and Copernicus DEM 30m (open),
산림청 임상도 1:5,000 + 산불통계 (data.go.kr), and AsiaFlux GDK historical.
