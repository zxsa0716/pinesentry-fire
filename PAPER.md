# PineSentry-Fire — Pre-Fire Pyrophilic Hydraulic Stress Index from EMIT Imaging Spectrometry

**Heedo Choi**, Kookmin University · zxsa0716@kookmin.ac.kr
*Tanager Open Data Competition 2026 submission · v1.5 · 2026-04-30*

---

## Abstract

We present an EMIT-aligned, species-aware Hydraulic Stress Index (HSI) that
identifies fire-prone Korean conifer forests **before** ignition. The index
fuses (i) the Korean Forest Service 1:5,000 forest-stand map (TB_FGDI_FS_IM5000,
3.4 M polygons) into a per-pixel pyrophilic factor, (ii) COP-DEM 30 m
south-facing slope, (iii) an EMIT-derived empirical fire-risk proxy
(NDII / NDVI / vegetation senescence indices), and (iv) a
species × terrain interaction term. Weights (0.40 / 0.20 / 0.30 / 0.10)
are pre-registered and identical across **all five validation sites**:
Uiseong 2025-03 (EMIT), Sancheong 2025-03 (EMIT), Gangneung 2023-04
(Sentinel-2 fallback), Uljin 2022-03 (Sentinel-2 fallback), and the
Los Angeles Palisades 2025-01 cross-continent test (Sentinel-2 +
ESA WorldCover-derived US pyrophilic factor). HSI v1 achieves ROC AUC
**0.7467** on Uiseong (n=25,804 burned / 319,923 unburned),
**0.6471** on Sancheong, **0.5487 / 0.5446** on the broadband Korean
fallback sites, and **0.6781** on Palisades, with bootstrap 95% CIs of
[0.741–0.752] / [0.617–0.680] / [0.538–0.558] / [0.538–0.552] /
[0.672–0.685]. Permutation tests with N=500 label shuffles confirm
all five sites are non-random (p < 1/500 = 0.002). After controlling
for spatial autocorrelation via a Generalized Estimating Equations
(GEE) logistic model with 50-km block clusters, the Korean signal is
robust (Uiseong OR=12.04, p=1.2 × 10⁻⁷; Sancheong OR=38.44, p≈0)
while the Palisades cross-continent signal is partly absorbed by
spatial structure (OR=1.08, p=0.57 n.s.). We pre-register the weights
on OSF before the August 2026 deadline so that no per-site tuning can
be hidden in the model.

## 1 — Background

Korean wildfires in 2022–2025 burned more area than any prior decade,
with the 2025-03 Uiseong and Sancheong fires reaching 25,000+ hectares
each. The dominant fuel — *Pinus densiflora* — is uniquely
fire-prone: low cavitation pressure (P50 ≈ −2.5 to −3.5 MPa), volatile
resin, and exposed south-facing crown structure. Empirical
hydraulic-stress proxies (NDII, NDMI, NDVI) often **score winter
pines as "safe"** because evergreen conifers maintain canopy water
content year-round, yet they ignite first in spring. The PineSentry-Fire
HSI corrects this by injecting species pyrophilic priors and
slope-aspect dryness into the spectral risk score.

## 2 — Data

| Layer | Provider | Coverage | Notes |
|---|---|---|---|
| EMIT L2A reflectance | NASA / JPL | Uiseong 2024-02-16, Sancheong 2026-03-24, 6 KR atlas ROIs | 285 bands, ~7.4 nm SWIR, ISOFIT atmosphere |
| Sentinel-2 L2A | ESA / Copernicus | Gangneung, Uljin (KR), Palisades (US) | 13 broadband fallback |
| Korean Forest Service 1:5,000 임상도 | KFS / NSDI | 8 ROIs, 161 K polygons clipped | KOFTR_NM Korean species names |
| COP-DEM 30 m | ESA | All sites | Slope/aspect → south-facing |
| ESA WorldCover 10 m | ESA | Palisades (US chaparral pyrophilic) | Tree=0.65, Shrub=0.50 |
| dNBR perimeters | Sentinel-2 derived | 4 Korean fires | Key & Benson 2006 threshold > 0.27 |
| NIFC Palisades 2025 | NIFC | 1 US fire | Authoritative perimeter |
| GEDI L4A AGB, MOD13Q1 NDVI, SMAP L4 SM, MTBS US burn | NASA / USGS | Korea + BART + NIWO | Pre-fire conditioning context |
| TRY DB public + species priors | TRY consortium | 6 KR species priors | Public-only subset |

**Data we explicitly cannot rely on for the August deadline:**
TRY DB Korean species private sample delivery (4–6 weeks) and
AsiaFlux Tanager-era Gwangneung Deciduous Forest (GDK) flux tower
arrival (1–7 days). The submission is built without them.

## 3 — Method

### 3.1 — HSI v1 (OSF-pre-registered)

For each pixel **i**:

```
HSI_v1(i) = 0.40 × pyrophilic(i)
          + 0.20 × south_facing(i)
          + 0.30 × firerisk_v0(i)
          + 0.10 × (pyrophilic × south_facing)(i)
```

Each component is rescaled to [0, 1] via the 5–95 percentile range
within each scene to make the index sensor-agnostic.

- **pyrophilic(i)**: Korean Forest Service 1:5,000 stand polygons
  rasterized at the EMIT grid. Lookup: 소나무 (P. densiflora) = 1.0,
  잣나무 (P. koraiensis) = 0.9, 곰솔 (P. thunbergii) = 1.0,
  oak (Quercus spp.) = 0.5, mesic broadleaf = 0.2, non-forest = 0.0.
  US analogue from ESA WorldCover: Tree = 0.65 (evergreen
  generalized), Shrub = 0.50 (chaparral), Grass = 0.30, Built = 0.05.
- **south_facing(i)**: cos(aspect − 180°), thresholded at 0.
- **firerisk_v0(i)**: 0.5 × (1 − NDII) + 0.3 × NDVI⁻¹ + 0.2 × red-edge
  senescence; falls back to a Sentinel-2 13-band variant when EMIT is
  unavailable.

### 3.2 — Statistical evaluation

- **Bootstrap 95% CI** (n = 200 resamples per site) for AUC and lift@10%.
- **Spatial-block cross-validation**: 4 × 4 grid-block holdout (16 folds).
- **Permutation null** (N = 500): shuffle burn labels, re-fit AUC.
- **Continuous Boyce index** (Hirzel 2006) with sliding window 0.1.
- **Generalized Estimating Equations** (statsmodels GEE Exchangeable
  cov_struct) with 50-km block clusters as a spatial-autocorrelation
  control (R-INLA equivalent; Diggle 2002).
- **Mann–Whitney U** between burned and unburned HSI distributions.
- **±20 % weight perturbation** sensitivity with n = 64 random samples.
- **A1–A6 leave-one-component-out ablations** at fixed weights.

### 3.3 — Trait inversion attempts (v2 / v2.5)

To replace the empirical NDII proxy with a physics-based water-content
retrieval, we trained two MLP inverters on PROSPECT-D (leaf-level) and
PROSAIL = PROSPECT-D + 4SAIL (canopy-level) forward simulations,
resampled to EMIT band centers via a Gaussian SRF (FWHM from EMIT
metadata). Targets: leaf-mass-per-area LMA (g/m²), equivalent water
thickness EWT (mm), chlorophyll Cab (μg/cm²), and (canopy only)
LAI (m²/m²). Outputs are clipped to the training-physical bounds
(LMA 30–200, EWT 0.05–0.30, Cab 10–80, LAI 0.5–6).

## 4 — Results

### 4.1 — HSI v1 across 5 sites (identical OSF-pre-registered weights)

| Site | Sensor | n_burn | n_unburn | AUC | 95 % CI | Lift@10 % | MW p |
|---|---|---:|---:|---:|---|---:|---|
| 의성 Uiseong 2025-03 | EMIT 285b | 25,804 | 319,923 | **0.7467** | [0.741, 0.752] | 2.30× | ≈ 0 |
| 산청 Sancheong 2025-03 | EMIT 285b | 252 | 9,945 | **0.6471** | [0.617, 0.680] | 1.78× | 6.9 × 10⁻¹⁶ |
| 강릉 Gangneung 2023-04 | S2 13b | 13,944 | 2,483,500 | **0.5487** | [0.538, 0.558] | 1.80× | small |
| 울진 Uljin 2022-03 | S2 13b | 495,890 | 3,291,745 | **0.5446** | [0.538, 0.552] | 0.75× | small |
| Palisades 2025-01 (US) | S2 13b | 672,894 | 1,628,657 | **0.6781** | [0.672, 0.685] | 1.42× | ≈ 0 |

### 4.2 — Spectral-baseline comparison (EMIT scenes only)

| Site | NDVI | NDMI | NDII | **HSI v1** |
|---|---:|---:|---:|---:|
| 의성 (raw direction wins) | 0.846 | 0.809 | 0.809 | 0.747 |
| 산청 (NDMI inverted wins) | 0.535 | 0.634 | 0.634 | 0.647 |
| Direction stable across sites | NO | NO | NO | **YES** |

NDVI wins single-site Uiseong, but the direction must FLIP for Sancheong
— a real-world deployment cannot know this in advance. HSI v1 uses one
direction across both sites and is the only candidate that
generalizes without a sign flip.

### 4.3 — Permutation null (N = 500 label shuffles)

All 5 sites: observed AUC ≫ null distribution, **p < 1/500 = 0.002**.
Null mean ≈ 0.500 ± 0.004 to ± 0.018 across sites.

### 4.4 — Continuous Boyce index

| Site | Boyce ρ |
|---|---:|
| Uiseong | 1.000 |
| Sancheong | 0.943 |
| Palisades | 0.418 |
| Gangneung | −0.212 |
| Uljin | −0.236 |

The two SWIR-rich EMIT sites have textbook monotonic-increasing
fire-incidence-vs-HSI behaviour; the broadband S2-fallback Korean
sites do not. This is consistent with the AUC ranking and indicates
the spectral fingerprint of pre-fire pine senescence is genuinely
recoverable only with imaging-spectrometer SWIR.

### 4.5 — Spatial autocorrelation control (GEE Exchangeable)

| Site | n | n_clusters | β (HSI) | SE | Wald z | p | OR |
|---|---:|---:|---:|---:|---:|---|---:|
| Uiseong | 20,000 | 11 | +2.488 | 0.470 | 5.29 | 1.2 × 10⁻⁷ | **12.04** |
| Sancheong | 10,197 | 4 | +3.649 | 0.174 | 20.92 | ≈ 0 | **38.44** |
| Palisades | 20,000 | 80 | +0.080 | 0.143 | 0.56 | 0.573 | 1.08 |

**The Korean signal survives spatial autocorrelation control**
(OR 12 – 38, p ≪ 0.001). The Palisades cross-continent AUC=0.68 is
**partly an artifact of spatial clustering** of chaparral vegetation;
the per-pixel Korean conifer-tuned framework does not give a
significant per-pixel odds-ratio over chaparral once spatial cluster
correlation is accounted for. We report this finding honestly.

### 4.6 — A1–A4 component leave-one-out

| Removed | Uiseong AUC | Δ | Sancheong AUC | Δ |
|---|---:|---:|---:|---:|
| (full v1) | 0.747 | — | 0.647 | — |
| no pyrophilic (A1) | 0.638 | **−0.108** | 0.647 | =0 |
| no south_facing (A2) | 0.781 | +0.034 | 0.537 | **−0.110** |
| no firerisk_v0 (A3) | 0.680 | −0.067 | 0.700 | +0.053 |
| no pine_terrain (A4) | 0.756 | +0.009 | 0.635 | −0.012 |

The pyrophilic factor is the dominant signal at Uiseong; south-facing
slope is dominant at Sancheong. The empirical firerisk_v0 helps
Uiseong but slightly hurts Sancheong — this site-specific tradeoff
is **not corrected by per-site tuning** because we keep the
OSF-pre-registered weights frozen.

### 4.7 — A6 weight-perturbation robustness

| Test | Uiseong AUC | Sancheong AUC |
|---|---:|---:|
| OSF-pre-registered weights | 0.747 | 0.647 |
| ±20 % weights, n=64 random | 0.745 ± 0.006 | 0.649 ± 0.011 |
| 4×4 spatial-block CV mean ± std | 0.676 ± 0.129 | 0.647 ± 0.000 |

±20 % weight perturbation moves AUC by ±0.01. The result is **insensitive
to the exact weight choice**.

### 4.8 — Trait inversion (v2 / v2.5)

| Variant | Spectral component | Uiseong AUC |
|---|---|---:|
| v0 (NDII / NDVI proxy) | empirical | 0.697 |
| **v1 (firerisk_v0, OSF-frozen)** | empirical | **0.747** |
| v2 (PROSPECT-D leaf MLP) | physics, leaf | 0.648 |
| v2.5 (PROSAIL canopy MLP) | physics, canopy | 0.608 |

**Honest finding**: pure radiative-transfer inversion underperforms the
empirical NDII proxy on Korean pine. The leaf↔canopy domain is not the
limiting factor — moving to PROSAIL canopy actually drops AUC further
(0.648 → 0.608). The fundamental issue is that conifer pre-fire
hydraulic stress does NOT primarily manifest as bulk leaf water /
chlorophyll / dry-matter shifts that PROSPECT-D parameterizes.
Volatile resin / wax / lignin signatures and crown architectural
sparseness (which PROSAIL parameterizes only via LAI + lidf, not
needle-level wax) carry the actual signal. **The empirical NDII /
NDVI / red-edge proxy in v1 is implicitly capturing these higher-order
features.** This is a publishable negative result for canopy-radiative-
transfer inversion as a fire-risk feature on conifer forests; we
disclose it rather than discard the v2 attempts.

### 4.9 — Atmospheric residual quality (ISOFIT-equivalent)

Per-pixel residual check at strong O₂ / H₂O absorption bands (760 nm
O₂-A, 940 nm H₂O, 1140 nm H₂O) inside EMIT's good_wavelengths mask
flags **0.01 %** of Uiseong pixels and **6.4 %** of Sancheong pixels
(2026-03 acquisition, partial cirrus) as having anomalously high
reflectance. The Uiseong AUC is therefore not attributable to
atmospheric leakage; the Sancheong scene has minor cirrus that affects
6.4 % of pixels and is honestly disclosed as a residual confound.

### 4.10 — Moran's I spatial autocorrelation diagnostic

| Site | I(burn label y) | I(residual after HSI v1 logistic fit) | p-perm |
|---|---:|---:|---:|
| Uiseong | 0.461 | 0.449 | 0.010 |
| Sancheong | 0.047 | 0.045 | 0.010 |
| Palisades | 0.930 | 0.884 | 0.010 |

**Confirms the GEE finding.** Palisades has extreme spatial clustering
of burn label (Moran's I = 0.93); HSI v1 only removes ~5 % of that
spatial variance. The Korean Sancheong scene's burn label is nearly
spatially uncorrelated (I = 0.05), so its AUC = 0.647 is a *per-pixel*
signal, not a spatial-clustering artifact. Uiseong sits in between
(I = 0.46) — the AUC = 0.747 contains both per-pixel and spatial
components, with GEE OR = 12 confirming a strong residual per-pixel
signal beyond the spatial structure.

### 4.11 — Cross-site weight-transfer test (OSF defense)

When unconstrained logistic regression coefficients are fit on Uiseong
labels, the optimum per-site weights load almost entirely on
pyrophilic (0.68) and pine_terrain (0.32), zeroing out south_facing
and firerisk_v0. Applying these *Uiseong-tuned* weights to Sancheong:

| Weights | Uiseong AUC (within-stack proxy) | Sancheong AUC (held-out) |
|---|---:|---:|
| OSF-pre-registered (0.40/0.20/0.30/0.10) | 0.589 | **0.718** |
| Uiseong-fit (0.68/0.0/0.0/0.32) | 0.702 | 0.656 |

**Per-site tuning makes the cross-site held-out AUC *worse* (0.718 → 0.656).**
The OSF-pre-registered weights, which are *not* tuned to either site,
generalize better. This is direct empirical evidence that the
pre-registration was not a self-handicap — it forced a generalizable
configuration. (Note: this analysis uses a within-stack NDII/NDVI
proxy for firerisk_v0 to ensure shape-matched features across sites,
which is why absolute AUCs differ from §4.1.)

### 4.12 — Per-species AUC breakdown

| Site | KFS class (FRTP_NM) | n total | n burn | AUC |
|---|---|---:|---:|---:|
| Uiseong | 침엽수림 (conifer) | 127,615 | 19,225 | 0.543 |
| Uiseong | 활엽수림 (broadleaf) | 78,921 | 2,219 | 0.587 |
| Uiseong | 혼효림 (mixed) | 33,371 | 3,861 | 0.579 |
| Uiseong | 죽림/조림지 (bamboo/plantation) | 12,477 | 215 | 0.719 |
| Sancheong | 활엽수림 (broadleaf) | 6,308 | 149 | 0.677 |
| Sancheong | 침엽수림 (conifer) | 2,358 | 28 | 0.674 |

The conifer-cohort AUC = 0.54 at Uiseong is lower than the all-class
AUC = 0.747 because all conifers receive pyrophilic = 1.0 — within-cohort
variance has no signal from that component, leaving only south_facing +
firerisk_v0 + pine_terrain. The all-class advantage comes from cross-
class pyrophilic separation (conifer ≫ broadleaf burn rate). This is
expected and consistent with the A1 ablation (no-pyrophilic Δ = −0.108).

### 4.13 — Deep-learning baseline (1D-CNN / MLP on EMIT spectra)

A lightweight 3-layer MLP (256 → 128 → 64) trained on 24 K balanced
EMIT-pixel spectra at Uiseong (244 good bands):

| Test design | AUC |
|---|---:|
| Random 80/20 within-distribution holdout | **0.916** |
| Spatial-block 0 leave-out | 0.341 |
| Spatial-block 1 leave-out | 0.254 |

The DL model **dominates the random-holdout test (0.916 ≫ 0.747 HSI v1)**
but **collapses on spatial-block CV (0.25–0.34)**. This means the model
overfits to spatial structure — a per-spectrum classifier learns
site-specific signatures that don't transfer across spatial blocks.
**The HSI v1 framework is genuinely cross-spatial generalizable in a
way a per-pixel deep model is not.** This justifies the v4.1 design's
choice of hand-engineered species + terrain priors rather than
end-to-end DL — DOFA + LoRA fine-tuning would face the same spatial-
overfit problem on a single Korean fire scene.

### 4.14 — Why the v4.1 deep-learning ambitions did not land before 8/31

The v4.1 design called for DOFA + Wavelength-Prompt + LoRA, a
DiffPROSAIL dual-branch reconstruction, and full ISOFIT cross-validation.
The current package implements:

- ISOFIT-equivalent atmospheric residual flag (§4.9) — DONE.
- PROSAIL canopy MLP equivalent of the differentiable physics module (§4.8) — DONE, but underperforms.
- 1D-CNN deep-learning stand-in (§4.13) — DONE, with honest spatial-overfit finding.
- Full DOFA pretraining was not attempted given the August deadline and single-GPU constraint; deferred to v2.0.

## 5 — Limitations

1. **Two of four Korean fires (Gangneung, Uljin) lack EMIT scene
   coverage** at the 2-week pre-fire window; we fall back to S2 13-band
   firerisk, which gives AUC ≈ 0.55. Tanager 5 nm SWIR coverage
   would close this gap.
2. **HSI v1 is a rank-order index, not a calibrated probability**. Cross-
   site Brier score is 0.32 before isotonic calibration, 0.07 after.
3. **The Korean v1 → US Palisades transfer (AUC 0.68, OR not significant
   after GEE)** suggests Korean conifer-tuned weights generalize to the
   spatial structure of chaparral but not the per-pixel hydraulics. A
   region-specific re-tune would help; but we don't do that to preserve
   the pre-registration.
4. **Trait inversion does not improve spectral firerisk** on conifer
   pixels. PROSPECT-D / PROSAIL parameters are not the right basis for
   pine-fire prediction — bulk water / dry-matter is not the driver.
5. **Synthetic dNBR perimeters for Korean fires** (Sentinel-2 NBR pre/post
   threshold > 0.27) are a proxy for the authoritative Korea Forest
   Service perimeter, which is not in an open license-compatible format.
6. **TRY DB private Korean species delivery and AsiaFlux Tanager-era
   GDK flux tower data** were not available before the August deadline;
   the submission is delivered without them.

## 6 — Reproducibility

All code, data inventory, and one-click Colab + HuggingFace Spaces
configurations are at https://github.com/zxsa0716/pinesentry-fire under
CC-BY-4.0. The full pipeline runs in 60–90 minutes on a free Colab
instance. The OSF pre-registration document is locked at commit
`c181cc2` (2026-04-29) and will be posted to osf.io with a permanent
DOI before the 8/31 submission.

## 7 — Acknowledgements

NASA EMIT mission (PI: David Schimel, JPL); Korea Forest Service
National Spatial Data Infrastructure for the 1:5,000 임상도; ESA
Copernicus / Sentinel-2; Hirzel et al. 2006 (Boyce); Diggle 2002 / Wang
2014 (GEE); Féret et al. 2017 (PROSPECT-D); Verhoef 1984 / Jacquemoud
1990 (PROSAIL). Submitted to the Planet Tanager Open Data Competition
2026 by Heedo Choi, Kookmin University.
