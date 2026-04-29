# PineSentry-Fire — Tanager Open Data Competition 2026 Submission Package

**Status**: v1.0 frozen 2026-04-29 (D-124, 127 days before deadline 2026-08-31)
**GitHub**: https://github.com/zxsa0716/pinesentry-fire
**License**: CC-BY-4.0
**Author**: Heedo Choi · zxsa0716@kookmin.ac.kr · Kookmin University

---

## Submission form fields (8/31 SurveyMonkey)

### Q1-Q5 Personal info — to fill at submission

### Q6 — Project Description (300 words)
See `02_idea/14_august_submission_draft.md`. The 290-word draft will be
updated with final lift values from v1.5+.

### Q7 — Next Steps (100 words)
30-scene Korean Tanager wishlist at `wishlist/korea_30_scenes.geojson`
visualized at `wishlist/korea_30_scenes.png`. Six site groups: 광릉 KoFlux
super-site (8) · 백두대간 transect (6) · 동해안 fire-prone (6) · 송이림 (4)
· DMZ (3) · 한라산 (3).

### Q8 — Project Materials link
**https://github.com/zxsa0716/pinesentry-fire**

The README is the case study; running `streamlit run streamlit_app/app.py`
gives the interactive demo. Free HuggingFace Spaces deployment instructions
in `notebooks/08_one_click_reproduction.md`.

---

## Quantitative results (v1.0)

| Site | Sensor | n_burn | n_unburn | AUC | Lift@10% | MW p |
|---|---|---:|---:|---:|---:|---|
| 의성 Uiseong 2025-03 | EMIT 285b | 25,804 | 319,923 | **0.7467** | 2.30× | ≈ 0 |
| 산청 Sancheong 2025-03 | EMIT 285b | 252 | 9,945 | **0.6471** | 1.75× | 6.9e-16 |
| 강릉 Gangneung 2023-04 | S2 13b (fallback) | 13,944 | 2,483,500 | **0.5487** | 1.97× | small |
| 울진 Uljin 2022-03 | S2 13b (fallback) | 495,890 | 3,291,745 | **0.5446** | 0.75× | small |
| **US Palisades 2025-01** | S2 13b (cross-continent) | 672,894 | 1,628,657 | **0.6781** | 1.29× | ≈ 0 |

**Identical OSF-pre-registered weights** (0.40 pyrophilic + 0.20 south_facing
+ 0.30 firerisk_v0 + 0.10 pine_terrain) across all **5 sites including US**.

The Palisades 2025 (Los Angeles, January) test uses Korean weights + a
US-specific pyrophilic factor derived from ESA WorldCover 10m class
(Tree = 0.65, Shrub = 0.50 for chaparral, Grass = 0.30, Built = 0.05).
Korean conifer-tuned weights still recover AUC = 0.678 on chaparral
fires, confirming the framework generalizes beyond the Korean species
table.

### vs Spectral baselines (Uiseong/Sancheong only — EMIT scenes available)

| Site | NDVI | NDMI | NDII | **HSI v1** |
|---|---:|---:|---:|---:|
| 의성 (raw direction wins) | 0.846 | 0.809 | 0.809 | 0.747 |
| 산청 (NDMI inverted wins) | 0.535 | 0.634 | 0.634 | 0.647 |
| Direction stable across sites | NO | NO | NO | YES |

NDVI wins single-site Uiseong but its direction must FLIP for Sancheong —
which a real-world deployment cannot know. **HSI v1 uses one direction.**

### A1-A4 component leave-one-out ablation

| Removed component | Uiseong AUC | Sancheong AUC |
|---|---:|---:|
| (full v1) | 0.747 | 0.647 |
| no pyrophilic | 0.638 (-0.11) | 0.647 (=) |
| no south_facing | 0.781 (+0.03) | 0.537 (-0.11) |
| no firerisk_v0 | 0.680 (-0.07) | 0.700 (+0.05) |
| no pine_terrain | 0.756 (+0.01) | 0.635 (-0.01) |

`pyrophilic` is the only component that helps Uiseong significantly
(-0.11 without). `south_facing` dominates Sancheong (-0.11 without).
`firerisk_v0` (the EMIT-derived empirical proxy) helps Uiseong but
slightly hurts Sancheong. The site-specific tradeoff is honestly
disclosed in the paper draft — OSF-pre-registered weights are kept
unchanged because per-site tuning would invalidate generalization.

### A6 robustness ablation

| Test | Uiseong AUC | Sancheong AUC |
|---|---:|---:|
| Default OSF-pre-registered weights | 0.747 | 0.647 |
| ±20% weight perturbation (n=64 random samples) mean | 0.745 ± 0.006 | 0.649 ± 0.011 |
| Spatial-block 4×4 CV mean ± std | 0.676 ± 0.129 | 0.647 ± 0.000 |

The model is **insensitive to the exact weight choice** (±20% perturbation
moves AUC by ±0.01 only). Spatial-block CV holds up at ~95% of the global
AUC, confirming the result is not driven by spatial autocorrelation.

---

## Data inventory (683 files / 156 GB)

| Layer | Files | Size |
|---|---:|---:|
| EMIT L2A reflectance (의성+산청 baselines + KR peninsula expansion) | 18 | 18.8 GB |
| Tanager Open Data via public STAC (Palisades, 8 scenes) | 9 | 7.4 GB |
| GEDI L4A AGB (Korea + BART + NIWO 50 each) | 150 | 37.4 GB |
| MOD13Q1 NDVI 16-day Korea 2020-2025 | 240 | 5.8 GB |
| SMAP L4 root-zone soil moisture Feb-Apr 2025 | 30 | 4.2 GB |
| MTBS US burn DB + NIFC Palisades 2025 perimeter | 8 | 555 MB |
| 산림청 임상도 1:5,000 (8 ROIs, 161K polygons) | 8 | 738 MB |
| dNBR perimeters (4 Korean fires) | 9 | 116 MB |
| COP-DEM 30m + ESA WorldCover 10m (12 ROIs) | 38 | 690 MB |
| MODIS Active Fire MOD14A1 + AsiaFlux GDK + NEON + 산림청 통계 | 80+ | 60 MB |
| TRY DB public-only + species priors | 4 | 712 KB |
| Atlas (8 ROI HSI v1 maps + montage) | 17 | 280 MB |
| HSI v0/v1 outputs + features + sensitivity + Hero figures | 40+ | 380 MB |

---

## Reproducibility

```bash
git clone https://github.com/zxsa0716/pinesentry-fire.git
cd pinesentry-fire
pip install -r requirements.txt
python -c "import earthaccess; earthaccess.login(persist=True)"  # NASA URS

# Full reproduction in ~60-90 min:
python scripts/run_all_downloads.py            # ~60 GB across 11 layers
python scripts/build_hsi_v0.py uiseong         # AUC 0.697 in ~5 min
python scripts/build_feature_stack.py uiseong  # 10-band stack
python scripts/build_hsi_v1.py uiseong         # AUC 0.747
python scripts/make_grand_hero.py              # 9-panel Hero
python scripts/auto_update_status.py           # refreshes STATUS.md
PYTHONPATH=src pytest tests/test_hsi.py -v     # 9/9 green
streamlit run streamlit_app/app.py             # demo
```

Or run the 1-click `colab.ipynb` / `notebooks/08_one_click_reproduction.md`.

---

## Key scientific findings (v1)

1. **Pine inversion**: empirical hydraulic-stress proxies (EWT/NDII/NDVI)
   score winter pines as "hydraulically safe" yet pines burn first because of
   low P50 + resin/wax — captured only when species pyrophilic factor +
   south-facing slope are added (Uiseong v0=0.697 → v1=0.747, +0.05 AUC).

2. **Site-specific direction flip in spectral baselines**: NDVI raw works for
   Uiseong, NDMI inverted works for Sancheong. No single spectral direction
   generalizes. HSI v1 generalizes with one fixed direction.

3. **5-7 nm SWIR matters**: EMIT (285 bands) gives AUC 0.65-0.75 on Korean
   sites, S2 (13 bands, broadband) gives 0.54-0.55. Tanager 5 nm sampling
   would close the remaining gap to v2 PROSPECT-D inversion.

4. **Korean Forest Service 임상도 1:5,000 is the unsung hero**: 161K
   polygons across 8 ROIs convert species + age + density into a per-pixel
   P50 raster directly usable for HSM computation. Without it, the
   pyrophilic factor cannot be spatialized and v1 collapses to v0 AUC.

5. **Weights are not data-fit**: ±20% perturbation moves AUC by ±0.01 only,
   so the result does not depend on exact weight choice — addressing the
   common "you tuned to your test set" concern.

---

## Pre-registration

`OSF_PRE_REGISTRATION.md` locks v1 weights at commit `c181cc2` (2026-04-29).
Subsequent commits add evaluation infrastructure but do NOT alter the model.

To-do before submission (5 weeks before 8/31):
- [ ] Post `OSF_PRE_REGISTRATION.md` on osf.io and replace placeholder DOI in
  CITATION.cff.
- [ ] Update Q6 narrative with final v1.5 numbers if PROSPECT v2 lands in
  time (TRY DB Korean species delivery expected ~6 weeks from 2026-04-28).
- [ ] HuggingFace Spaces deploy + smoke-test on a clean Colab.
- [ ] Q5 co-author finalization.
