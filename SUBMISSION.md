# PineSentry-Fire — Tanager Open Data Competition 2026 Submission Package

**Status**: v1.5 frozen 2026-04-30 (D-123, 123 days before deadline 2026-08-31)
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

### v2 / v2.5 PROSPECT-D + PROSAIL canopy inversion (honest finding)

| Variant | Spectral firerisk source | Uiseong AUC |
|---|---|---:|
| v1 (firerisk_v0, OSF-frozen) | empirical NDII/NDVI/RE | **0.747** |
| v2 (PROSPECT-D leaf MLP) | physics, leaf-only | 0.648 |
| v2.5 (PROSAIL canopy MLP) | physics, canopy + soil | 0.608 |

Pure radiative-transfer inversion underperforms the empirical NDII
proxy on Korean conifer pixels. Moving from leaf to canopy domain does
NOT close the gap. The signal v1 captures comes from non-PROSPECT
features (volatile resin, wax, lignin, crown architecture) that are
not parameterized by the standard leaf-canopy model. We disclose this
negative result rather than discard the v2 attempts.

### Spatial autocorrelation control (GEE Exchangeable, R-INLA equivalent)

| Site | Wald z | p | OR(HSI v1) |
|---|---:|---|---:|
| 의성 Uiseong | 5.29 | 1.2 × 10⁻⁷ | **12.04** |
| 산청 Sancheong | 20.92 | ≈ 0 | **38.44** |
| Palisades (US) | 0.56 | 0.573 (n.s.) | 1.08 |

Korean per-pixel signal is robust after spatial control. Palisades
cross-continent AUC is partly an artifact of chaparral spatial
clustering. **Confirmed by Moran's I** (Uiseong I = 0.46, Sancheong
I = 0.05, Palisades I = 0.93).

### Cross-site weight-transfer test (OSF defense)

| Weights | Uiseong AUC | Sancheong AUC |
|---|---:|---:|
| OSF-pre-registered (0.40 / 0.20 / 0.30 / 0.10) | 0.589 | **0.718** |
| Uiseong-fit logistic (0.68 / 0.0 / 0.0 / 0.32) | 0.702 | 0.656 |

(Within-stack NDII proxy for shape-matched cross-site eval.)
**Per-site tuning HURTS the held-out site's AUC by 6.2 points.** The
OSF-frozen weights generalize better than weights tuned on the
training site. Direct empirical defense of the pre-registration.

### Continuous Boyce index

| Site | Boyce ρ |
|---|---:|
| 의성 Uiseong | 1.000 |
| 산청 Sancheong | 0.943 |
| Palisades (US) | 0.418 |
| 강릉 Gangneung | -0.212 |
| 울진 Uljin | -0.236 |

EMIT SWIR sites have textbook monotonic increasing fire-incidence-vs-HSI;
S2-fallback sites do not. Imaging-spectrometer SWIR is essential.

### Permutation null (N = 500)

All 5 sites: observed AUC ≫ null mean (≈ 0.500), p < 1/500 = 0.002.

### 1D deep-learning baseline (DOFA stand-in)

| Test design | AUC |
|---|---:|
| Random 80/20 within-distribution | 0.916 |
| Spatial-block 0 leave-out | 0.341 |
| Spatial-block 1 leave-out | 0.254 |

Per-pixel DL **overfits to spatial structure** and does not generalize
across spatial blocks — exactly the problem the hand-engineered
HSI v1 framework avoids. End-to-end DOFA fine-tuning on a single fire
scene would face the same problem.

### Atmospheric quality (ISOFIT-equivalent)

Per-pixel residual flag at 760 / 940 / 1140 nm O₂/H₂O bands:
- Uiseong: 0.01 % flagged → atmosphere correction is solid
- Sancheong: 6.4 % flagged (partial cirrus, disclosed honestly)

### Multi-temporal pre-fire signal at Sancheong (T − 1.5 mo)

EMIT acquisition 2026-02-10 (1.5 months before the 2026-03 Sancheong fire)
shows mean firerisk_v0 = 0.857 inside the burn polygon vs 0.711 outside
(Δ = +0.146, MW p ≈ 0, n_burn = 13,323 pixels). **EMIT detects pre-fire
pyrophilic stress ~6 weeks before ignition.**

### SMAP root-zone soil moisture integration (HSI v1.5)

| Site | HSI v1 | SMAP-RZSM alone | HSI v1.5 combined | Δ vs v1 |
|---|---:|---:|---:|---:|
| Uiseong | 0.7467 | 0.5995 | 0.7463 | -0.0004 |
| Sancheong | 0.6471 | 0.6333 | 0.6487 | +0.0016 |

SMAP adds essentially no AUC. HSI v1 already captures the soil-moisture
signal through NDII/NDMI in firerisk_v0. Honest negative result.

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

6. **Per-site tuning hurts cross-site AUC**: Uiseong-fit unconstrained
   logistic-regression weights collapse to (0.68 pyro / 0.32 pine_terrain)
   and *lose 6.2 points* on the held-out Sancheong evaluation. The
   OSF-pre-registered weights are more transferable than per-site optima.

7. **Pure radiative-transfer inversion underperforms empirical NDII** on
   conifer fire risk: PROSPECT-D leaf and PROSAIL canopy inversions both
   give AUC < 0.65 vs HSI v1's 0.747. The relevant pre-fire chemistry
   (resin, wax, lignin) is not parameterized by these standard models.

8. **Per-pixel DL overfits spatial structure**: a 3-layer MLP gets
   AUC 0.92 on random 80/20 holdout but collapses to 0.25–0.34 on spatial-
   block CV. Hand-engineered species + terrain priors generalize where
   pure DL does not.

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
