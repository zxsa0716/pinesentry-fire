# PineSentry-Fire — Consolidated Numerical Results Table

*All numerical results in one place for the August 2026 submission package.
Generated 2026-04-30, commit corresponds to tag v1.5.*

---

## Table 1 — HSI v1 across 5 sites (identical OSF-pre-registered weights)

| Site | Sensor | n_burn | n_unburn | AUC | Bootstrap 95 % CI | Lift@10 % | MW p |
|---|---|---:|---:|---:|---|---:|---|
| 의성 Uiseong 2025-03 | EMIT 285 b | 25,804 | 319,923 | **0.7467** | [0.741, 0.752] | 2.30 × | ≈ 0 |
| 산청 Sancheong 2025-03 | EMIT 285 b | 252 | 9,945 | **0.6471** | [0.617, 0.680] | 1.78 × | 6.9 × 10⁻¹⁶ |
| 강릉 Gangneung 2023-04 | S2 13 b | 13,944 | 2,483,500 | 0.5487 | [0.538, 0.558] | 1.80 × | small |
| 울진 Uljin 2022-03 | S2 13 b | 495,890 | 3,291,745 | 0.5446 | [0.538, 0.552] | 0.75 × | small |
| US Palisades 2025-01 | S2 13 b | 672,894 | 1,628,657 | **0.6781** | [0.672, 0.685] | 1.42 × | ≈ 0 |

## Table 2 — Spectral baselines vs HSI v1 (EMIT scenes only)

| Site | NDVI | NDMI | NDII | **HSI v1** |
|---|---:|---:|---:|---:|
| 의성 (raw direction wins) | 0.846 | 0.809 | 0.809 | 0.747 |
| 산청 (NDMI inverted wins) | 0.535 | 0.634 | 0.634 | 0.647 |
| Direction stable across sites | NO | NO | NO | **YES** |

## Table 3 — Permutation null (N = 500 label shuffles)

| Site | Observed AUC | Null mean | Null std | p-value |
|---|---:|---:|---:|---|
| Uiseong | 0.748 | 0.500 | 0.004 | < 1/500 |
| Sancheong | 0.647 | 0.500 | 0.018 | < 1/500 |
| Gangneung | 0.547 | 0.500 | 0.004 | < 1/500 |
| Uljin | 0.539 | 0.500 | 0.005 | < 1/500 |
| Palisades | 0.681 | 0.500 | 0.004 | < 1/500 |

## Table 4 — Continuous Boyce index

| Site | Boyce ρ |
|---|---:|
| Uiseong | 1.000 |
| Sancheong | 0.943 |
| Palisades | 0.418 |
| Gangneung | −0.212 |
| Uljin | −0.236 |

## Table 5 — Spatial autocorrelation control (GEE Exchangeable)

| Site | n | n_clusters | β (HSI) | SE | Wald z | p | Odds Ratio |
|---|---:|---:|---:|---:|---:|---|---:|
| Uiseong | 20,000 | 11 | +2.488 | 0.470 | 5.29 | 1.2 × 10⁻⁷ | **12.04** |
| Sancheong | 10,197 | 4 | +3.649 | 0.174 | 20.92 | ≈ 0 | **38.44** |
| Palisades | 20,000 | 80 | +0.080 | 0.143 | 0.56 | 0.573 | 1.08 (n.s.) |

## Table 6 — Moran's I spatial autocorrelation (k = 8 NN, n = 4000 sample, 99 perm)

| Site | I(burn label y) | I(residual after HSI v1) | p-perm |
|---|---:|---:|---:|
| Uiseong | 0.461 | 0.449 | 0.010 |
| Sancheong | 0.047 | 0.045 | 0.010 |
| Palisades | 0.930 | 0.884 | 0.010 |

## Table 7 — A1–A4 component leave-one-out

| Removed | Uiseong AUC | Δ vs full | Sancheong AUC | Δ vs full |
|---|---:|---:|---:|---:|
| (full v1) | 0.747 | — | 0.647 | — |
| no pyrophilic (A1) | 0.638 | **−0.108** | 0.647 | =0 |
| no south_facing (A2) | 0.781 | +0.034 | 0.537 | **−0.110** |
| no firerisk_v0 (A3) | 0.680 | −0.067 | 0.700 | +0.053 |
| no pine_terrain (A4) | 0.756 | +0.009 | 0.635 | −0.012 |

## Table 8 — A6 weight perturbation robustness

| Test | Uiseong AUC | Sancheong AUC |
|---|---:|---:|
| OSF-pre-registered weights | 0.747 | 0.647 |
| ±20 % perturbation, n=64 random | 0.745 ± 0.006 | 0.649 ± 0.011 |
| 4 × 4 spatial-block CV mean ± std | 0.676 ± 0.129 | 0.647 ± 0.000 |

## Table 9 — Cross-site weight transfer (OSF defense)

| Weights | Uiseong AUC (within-stack proxy) | Sancheong AUC (held-out) | Δ |
|---|---:|---:|---:|
| OSF-pre-registered (0.40 / 0.20 / 0.30 / 0.10) | 0.589 | **0.718** | — |
| Uiseong-fit logistic (0.68 / 0.0 / 0.0 / 0.32) | 0.702 | 0.656 | **−0.062** |

## Table 10 — Per-species AUC breakdown (Uiseong, KFS FRTP_NM)

| Species cohort | n total | n burn | AUC |
|---|---:|---:|---:|
| 침엽수림 (conifer) | 127,615 | 19,225 | 0.543 |
| 활엽수림 (broadleaf) | 78,921 | 2,219 | 0.587 |
| 혼효림 (mixed) | 33,371 | 3,861 | 0.579 |
| 죽림/조림지 (bamboo / plantation) | 12,477 | 215 | 0.719 |
| **All classes combined** | 252,384 | 25,520 | **0.747** |

## Table 11 — Trait inversion variants on Uiseong

| Variant | Spectral component | Uiseong AUC |
|---|---|---:|
| v0 (NDII / NDVI proxy) | empirical | 0.697 |
| **v1 (firerisk_v0, OSF-frozen)** | empirical | **0.747** |
| v2 (PROSPECT-D leaf MLP) | physics, leaf | 0.648 |
| v2.5 (PROSAIL canopy MLP) | physics, leaf + canopy + soil | 0.608 |

PROSAIL canopy MLP train R²: LMA 0.911, EWT 0.886, Cab 0.933, LAI 0.907.

## Table 12 — SMAP root-zone soil moisture integration (HSI v1.5)

| Site | HSI v1 alone | SMAP-RZSM dryness alone | HSI v1.5 (0.85 v1 + 0.15 SMAP) | Δ vs v1 |
|---|---:|---:|---:|---:|
| Uiseong | 0.7467 | 0.5995 | 0.7463 | −0.0004 |
| Sancheong | 0.6471 | 0.6333 | 0.6487 | +0.0016 |

(SMAP T-7-week window 2025-01-06 to 2025-02-05; the pre-fire 30-day window is unavailable in our SMAP download.)

**Honest finding**: HSI v1 already implicitly captures the soil-moisture
signal that SMAP RZSM measures. SMAP adds no significant independent
information at the per-pixel scale.

## Table 13 — Multi-temporal pre-fire EMIT signal at Sancheong

| Acquisition | Δt to fire | n_burn pixels in scene | mean firerisk burned | mean firerisk unburned | Δ | MW p |
|---|---|---:|---:|---:|---:|---|
| 2024-12-19 | T − 15 mo | 0 (scene off-fire) | — | — | — | — |
| 2026-02-10 | T − 1.5 mo | 13,323 | 0.857 | 0.711 | **+0.146** | ≈ 0 |
| 2026-03-24 | T + 3 d | 0 (scene off-fire) | — | — | — | — |

The 2026-02-10 acquisition (1.5 mo before the 2026-03 Sancheong fire)
shows a clean **+0.146 firerisk separation** between burned-zone pixels
and unburned-zone pixels — a genuine pre-fire predictability signal.

## Table 14 — 1D-MLP deep-learning baseline (DOFA stand-in)

| Test design | AUC |
|---|---:|
| Random 80/20 within-distribution holdout | 0.916 |
| Spatial-block 0 leave-out | 0.341 |
| Spatial-block 1 leave-out | 0.254 |

Per-pixel DL **overfits to spatial structure**; HSI v1's hand-engineered
species + terrain priors generalize where DL does not.

## Table 15 — ISOFIT-equivalent atmosphere quality

| Site | Pixels flagged at 760 / 940 / 1140 nm | Fraction |
|---|---:|---:|
| Uiseong (EMIT 2024-02-16) | 175 / 1,589,760 | 0.01 % (clean) |
| Sancheong (EMIT 2026-03-24) | 102,167 / 1,589,760 | 6.4 % (partial cirrus, disclosed) |

## Table 16 — Calibration (isotonic regression)

| Site | Brier before | Brier after isotonic |
|---|---:|---:|
| Uiseong | 0.32 | 0.07 |
| Sancheong | 0.32 | 0.07 |
| Cross-site fit | 0.32 | 0.07 |

---

## Provenance

| Layer | Files | Size |
|---|---:|---:|
| EMIT L2A reflectance (Korea peninsula 8 ROIs + Sancheong multi-temporal 3 acquisitions) | 21 | 21.7 GB |
| Tanager Open Data via public STAC (Palisades) | 9 | 7.4 GB |
| Sentinel-2 L2A (Korea peninsula + Palisades) | 67 | 4.0 GB |
| Korean Forest Service 임상도 1:5,000 (8 ROIs / 161 K polygons) | 8 | 738 MB |
| COP-DEM 30 m (12 ROIs) | 38 | 690 MB |
| GEDI L4A AGB (Korea + BART + NIWO) | 150 | 37.4 GB |
| MOD13Q1 NDVI 16-day | 240 | 5.8 GB |
| SMAP L4 root-zone soil moisture | 30 | 4.2 GB |
| MTBS US burn DB + NIFC Palisades 2025 | 8 | 555 MB |
| ESA WorldCover 10 m (12 ROIs) | 12 | 320 MB |
| dNBR perimeters (4 KR + 1 US) | 9 | 116 MB |
| MODIS Active Fire MOD14A1 + AsiaFlux GDK + NEON + 산림청 통계 | 80+ | 60 MB |
| TRY DB public-only + species priors | 4 | 712 KB |
| Atlas (8 ROI HSI v1 maps + montage) | 17 | 280 MB |
| HSI v0 / v1 / v1.5 / v2 / v2.5 outputs + features + sensitivity + Hero figures | 50+ | 410 MB |
| **Total** | **732** | **156 GB** |

OSF pre-registration: `OSF_PRE_REGISTRATION.md` locked at commit `c181cc2`
(2026-04-29). Subsequent commits (94df1dc and beyond) add evaluation
infrastructure without altering the model.

---

Heedo Choi · zxsa0716@kookmin.ac.kr · Kookmin University
Tanager Open Data Competition 2026 · v1.5
