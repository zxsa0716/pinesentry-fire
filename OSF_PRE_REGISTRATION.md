# OSF Pre-Registration Document — PineSentry-Fire v4.1

> Submit to OSF (https://osf.io) **BEFORE** running validation on Korean Hero scenes (의성, 산청).
> This document locks the analysis specification to prevent post-hoc fitting.
> Target submission date: 2026-05-15 (before Week 7 US validation).

---

## Title

**PineSentry-Fire: Tanager-Trained Hydraulic Stress Index for Pre-Fire Functional Trait Detection in Korean Pinus densiflora Forests**

## Authors

(Filled at submission.)

## Pre-Registration Date

YYYY-MM-DD

---

## 1. Hypotheses

**H1**: At Sentinel-2 13-band spectral resolution, foliar nitrogen change ΔN ≥ 0.3 wt% in *Pinus densiflora* canopies cannot be detected; at Tanager 5-nm × 426-band resolution, it can.

**H2**: A wavelength-aware DOFA backbone trained on global Tanager forest scenes transfers to EMIT (60 m × 285 bd) over Korean forests with leaf-trait retrieval RMSE ≤ 10 % of the trait dynamic range.

**H3**: At the 의성 (Uiseong, 2025-03-22) and 산청 (Sancheong, 2025-03-21) wildfire sites, the Hydraulic Stress Index (HSI) computed on EMIT pre-fire scenes is positively associated with within-perimeter pixels relative to unburned reference, controlling for forest type, age, slope, aspect, elevation, distance-to-road, and 30-day cumulative VPD. The expected odds ratio (top vs. bottom HSI tertile) is ≥ 1.5 with 95 % CI excluding 1, after spatial block cross-validation.

---

## 2. HSI Definition (LOCKED — DO NOT MODIFY AFTER PRE-REGISTRATION)

```
HSI = w_safety · (1 − HSM_norm) + w_water · (1 − EWT_norm) + w_starch · LMA_norm

HSM = P_50(species) − Ψ_min                  (Martin-StPaul 2017 Ecol Lett)
Ψ_min ≈ −0.3 / EWT_mm − 1.5                  (Sack & Holbrook 2006 simplified)
HSM_norm, EWT_norm, LMA_norm: 5–95 percentile-clipped within site

w_safety = 0.5
w_water  = 0.3
w_starch = 0.2
```

P_50 species lookup from TRY DB (Pinus densiflora ≈ −3.0 MPa, Quercus mongolica ≈ −2.5 MPa, default −2.7 MPa).

**No data-driven weight tuning is permitted on Korean Hero scenes.** A6 sensitivity analysis (±50 % weight perturbation) is the only post-hoc weight exploration allowed and must be reported transparently.

---

## 3. Target Datasets (LOCKED)

- **Tanager training**: 5 global Open Data Catalog scenes (NEON Bartlett, NEON Niwot, Park Fire 2024, LA Palisades 2025, Tapajós).
- **EMIT validation Korea (Hero)**: pre-registered granule IDs:
  - 의성 baseline: `EMIT_L2A_RFL_001_20240216T044207_2404703_007` (T-13mo, cc=21 %)
  - 의성 long baseline: `EMIT_L2A_RFL_001_20230131T040951_2303103_004` (T-414d, cc=28 %)
  - 산청 most-recent: `EMIT_L2A_RFL_001_20241219T032003_2435402_004` (T-3mo, cc=37 %)
  - 산청 1-yr lag: `EMIT_L2A_RFL_001_20240331T035456_2409103_004` (T-12mo, cc=38 %)
  - 산청 dry baseline: `EMIT_L2A_RFL_001_20230225T015309_2305601_002` (T-25mo, cc=35 %)
- **US Hero**: LA Palisades 2025-01-07; pre-fire Tanager scenes since 2024-08.
- **Validation**: KoFlux GDK 2024-08 ~ 2026-04 (광릉), GEDI L4A AGB, 산림청 임상도, 산불 GIS perimeters (산림청, 의성·산청 2025).

---

## 4. Analysis Plan (LOCKED)

### 4.1 Sample design
- **Spatial block CV**: 1 km × 1 km blocks, 5-fold; folds drawn at random with seed 42.
- **Case-control sampling**: 1:5 (burn pixels : reference pixels). Reference pixels drawn from same block but outside perimeter, matched on forest-type and slope.
- **Class imbalance handling**: report PR-AUC + Brier score in addition to ROC-AUC.

### 4.2 Statistical model
- **Spatial logistic GLMM** (R-INLA): logit(P_burn) = β_0 + β_HSI · HSI + Σ β_k · X_k + spatial_RE + residual.
- Covariates X: forest type (categorical from 임상도), age class, slope (continuous), aspect (sin/cos), elevation, distance-to-road, distance-to-village, 30-day prior VPD.
- Spatial RE: SPDE on 1 km mesh.
- Inference: posterior odds ratio with 95 % credible interval.

### 4.3 Permutation test
- 1000 random shuffles of HSI labels within each spatial block.
- Report empirical p-value of observed AUC vs null distribution.

### 4.4 Baseline comparison (mandatory)
ROC + PR curves overlaid for HSI, KBDI, FWI (ECMWF), Korean DWI (산림청), NDMI, NDVI difference, on the same Korean Hero pixels. Report ΔAUC and Boyce index.

### 4.5 Ablations
- A1: Sentinel-2 13-band binned vs Tanager full
- A2: Tanager full vs SWIR-only vs VNIR-only
- A3: DiffPROSAIL on/off (γ ∈ {0, 0.5, 1.0})
- A4: Tanager-only train vs EMIT cross-sensor transfer
- A5: HSI vs each single trait (LMA / EWT / N / lignin / REIP)
- A6: HSI weight ±50 % sensitivity (1000 random samples)

### 4.6 Decision criteria
- H3 confirmed if **odds ratio (top vs bottom HSI tertile) ≥ 1.5 with 95 % CI > 1** AND HSI ROC-AUC exceeds the best of {KBDI, FWI, DWI, NDMI, NDVI} by ≥ 0.05.
- If criteria fail, report negative result honestly; do not retune weights.

---

## 5. Stopping Rules

- If EMIT pre-fire scenes for both 의성 and 산청 are unusable due to clouds, fall back to single-Hero (whichever passes) or US-only narrative; **do not change H1-H3 statements**.
- If H3 fails, report transparent negative result and reframe the contribution as the trait-retrieval engine + KoFlux NEE × HSI Validation (still publishable).

---

## 6. Public Materials

- GitHub repo (frozen at submission): https://github.com/[user]/pinesentry-fire (commit hash recorded)
- Zenodo DOI: pending Week 14
- This pre-registration: OSF DOI pending

---

## 7. Investigator Statement

I confirm that:
- HSI weights are fixed before any Korean Hero analysis.
- Spatial block CV folds are seeded before fitting.
- Baseline indices are computed on the same pixels before HSI.
- All ablations are reported regardless of outcome.

**Signed**: , [Date]

---

*This pre-registration follows the OSF "AsPredicted"-style template with adaptations for spatial remote-sensing analyses (Roberts et al. 2017 Ecography for spatial CV; Phillips & Elith 2013 Ecology for case-control design).*
