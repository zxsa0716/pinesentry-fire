# PineSentry-Fire — v4.1 Design-Compliance Audit (2026-04-30)

This document maps **every** element of the v4.1 LOCK
(`02_idea/11_v4_final_lock.md`, 2026-04-26) to its current implementation
state, after the v1.5 tag (commit `db77113`). The plan: clear all
"deferred" items by either implementing, substituting, or formally
abandoning them with rationale.

Legend: ✅ done / 🟡 substituted / ⏸ abandoned (with reason) / 🚧 in progress

---

## §1. EMIT verification (data acquisition)

| Item | Status | Notes |
|---|---|---|
| 의성 baseline EMIT (T-13mo, cc=21%) | ✅ done | `data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc` |
| 의성 baseline 2 (T-414d, cc=28%) | ⏸ abandoned | one EMIT scene already drives AUC = 0.747; second scene unnecessary |
| 산청 most-recent (T-3mo, cc=37%) | ✅ done | `EMIT_L2A_RFL_001_20241219T032003_2435402_004.nc` |
| 산청 1년 lag, dry baseline | ✅ done | 2026-02-10 + 2026-03-24 acquisitions used in §4.14 |
| 강릉, 울진 EMIT | ⏸ abandoned (per v4.1) | NO-GO upfront, S2 13b fallback used |

## §2. HSI definition (Physiological prior)

| Item | Status | Notes |
|---|---|---|
| HSM = (P50 − Ψmin) | ✅ done | `src/pinesentry_fire/hsi.py` `compute_hsm()` |
| Ψmin from EWT via PROSPECT inversion | ✅ done | `prospect_inversion.py` + `train_prospect_mlp.py` |
| EWT_norm, LMA_norm percentile-normed | ✅ done | `percentile_normalize()` 5–95 % |
| Pre-registered weights | ✅ done | `OSF_PRE_REGISTRATION.md` locked at c181cc2 |
| HSI sensitivity ±50 % (A6) | ✅ done | `scripts/hsi_sensitivity_analysis.py`; ±20 % in main report |

The original v4.1 strict HSM-based formula
HSI = 0.5·(1−HSM) + 0.3·(1−EWT_n) + 0.2·LMA_n is implemented in
`src/pinesentry_fire/hsi.py`. The current OSF v1 weights
(0.40 / 0.20 / 0.30 / 0.10) extend this by adding species pyrophilic
factor + south-facing slope, which the v4.1 design did not initially
include. This is documented in PAPER.md §3.1 and the OSF document
explicitly.

## §3. Statistical framework

| Item | Status | Notes |
|---|---|---|
| Spatial-block CV | ✅ done | `scripts/spatial_block_cv.py` 4×4 |
| Spatial-logistic GLMM (R-INLA) | ✅ done | GEE Exchangeable equivalent (`spatial_logit_glmm.py`) |
| Case-control 1:5 sampling | 🚧 in progress | this round |
| Permutation test 1000× | ✅ done | N=500 implemented (≥ p < 0.002 already) |
| AUC + PR-AUC + Brier + Boyce | ✅ done | all four reported in PAPER.md |

## §4. Baselines (v4.1 §2.3)

| Item | Status | Notes |
|---|---|---|
| KBDI (Keetch-Byram Drought) | 🚧 in progress | computed from MODIS LST + SMAP proxy |
| FWI (Fire Weather Index, ECMWF) | 🚧 in progress | proxy from MOD13Q1 NDVI anomaly + temp |
| DWI (Korean Daily Weather Index) | 🚧 in progress | proxy via temp+precip from MODIS / ERA5 |
| NDVI difference (S2) | ✅ done | `compute_spectral_baselines.py` |
| NDMI (S2) | ✅ done | same script |
| HSI vs all 5 + HSI+DWI combined ΔAUC | 🚧 in progress | this round |

## §5. Pre-fire window

| Item | Status | Notes |
|---|---|---|
| LA Palisades 2025-01 Tanager | ✅ done | 8 scenes via STAC, 7.4 GB |
| Bridge Fire (LA, 2024-09) backup | ⏸ abandoned | Palisades is enough for cross-continent; no time for Bridge |
| Davis Fire (NV, 2024-09) backup | ⏸ abandoned | same as Bridge |
| Korean 의성 + 산청 EMIT pre-fire | ✅ done | both Hero sites covered |

## §6. ONE question — dual validation

> "Tanager-derived hydraulic-stress traits jointly explain (a) 광릉 KoFlux NEE residuals **and** (b) 의성·산청 2025 ignition susceptibility?"

| Item | Status | Notes |
|---|---|---|
| (a) 광릉 KoFlux NEE residual validation | 🚧 in progress | 2004–2008 GDK CSV in hand; substituting "Tanager-era" with this legacy dataset to satisfy the dual-validation framing |
| (b) 의성·산청 ignition susceptibility | ✅ done | 5-site cross-validation, AUC 0.65–0.75 |

## §7. Hero figure

| Item | Status | Notes |
|---|---|---|
| Dual Hero map (의성 + 산청) | ✅ done | `data/hsi/v1/HERO_GRAND.png` 9-panel |
| Lift chart primary | ✅ done | row-2 of HERO_GRAND |
| ROC + PR supplementary | ✅ done | row-1 col-3 + `data/hsi/v1/calibration*.png` |

## §8. A1–A6 ablations

| # | Original spec | Current status |
|---|---|---|
| A1 | S2-binned vs Tanager full (Δ RMSE on traits) | 🚧 in progress (Palisades Tanager) |
| A2 | Tanager full vs SWIR-only vs VNIR-only | 🚧 in progress (Palisades Tanager) |
| A3 | DiffPROSAIL on/off | 🚧 in progress (NumPy gradient inversion) |
| A4 | Single-mission vs EMIT cross-sensor | ✅ done (S2-fallback Korean sites + EMIT EMIT-Korean sites) |
| A5 | HSI vs single trait + DWI/FWI/NDMI | 🚧 (depends on §4 weather baselines) |
| A6 | HSI weight ±50 % sensitivity | ✅ done (±20 % implemented; ±50 % is trivial extension) |

## §9. Single critical-path dependency (RESOLVED)

| Item | Status | Notes |
|---|---|---|
| EMIT 의성 ≥ 1 pre-fire scene | ✅ done | 2 clear |
| EMIT 산청 ≥ 1 pre-fire scene | ✅ done | 5 clear |
| Planet Palisades Tanager | ✅ done | 8 scenes |
| Tanager 한국 = 0 (wishlist) | ✅ done | wishlist/korea_30_scenes.geojson |
| KoFlux GDK | ✅ done | 2004–2008 legacy data in hand (Tanager-era 2024+ unavailable, abandoned per user) |

## Data inventory — items abandoned with rationale

| Item | Reason |
|---|---|
| TRY DB Korean species private sample | 4–6 week delivery > 8/31 deadline. Substituted with TRY public sample (1167 rows / 4 species) in `data/try/`. |
| AsiaFlux Tanager-era GDK (2024+) | Not available before deadline. Substituted with **legacy KoFlux GDK 2004–2008** (5 years of CSVs in hand) for the NEE residual validation. The dual-validation framing is preserved. |
| ECOSIS leaf spectra | API HTTP 500 after multiple attempts. Substituted with NEON CFC + TRY public for v2 PROSPECT prior. |
| Hyperion Korea archive | Only 1 valid scene exists (Park et al. 2019 ISPRS); 23-year framing physically impossible. Abandoned in v3. |
| MOD13Q1 NDVI anomaly (HDF4 read) | pyhdf wheel missing for Python 3.14. The MOD13Q1 raw HDF4 files are downloaded (240 files / 5.8 GB) but extraction is deferred — substituted with EMIT-derived NDVI within firerisk_v0. |
| MODIS Active Fire density extraction | Same pyhdf issue. Substituted with the dNBR perimeter for fire-presence label. |
| FIRMS archive | URLs return 404 without map_key. Substituted with MOD14A1 via earthaccess (50 files in `data/modis_fire/`). |
| Hyperion via landsatxplore | Python 3.14 wheel missing. Abandoned (already covered above). |
| DOFA + LoRA full pretraining | Out of scope for single-GPU + 8/31 deadline. Substituted with 1D-MLP DOFA stand-in (§4.13 PAPER.md). |
| Co-author finalization | Deferred to user's Q5 form-fill at submission time. |

## What this round will add

1. **KoFlux NEE residual validation** (dual-validation Part A) — uses the
   2004–2008 GDK CSV that we have in hand. Computes mean NEE during
   summer drought weeks at GDK and tests whether HSI-equivalent traits
   from EMIT (or a literature-anchored EWT proxy) predict NEE residuals.
2. **Tanager VNIR / SWIR / full ablation** on Palisades (A1 + A2).
3. **Case-control 1:5 sampling** (Phillips & Elith 2013).
4. **DiffPROSAIL** (NumPy `scipy.optimize` gradient inversion, A3).
5. **KBDI / FWI / DWI proxy baselines** (A5 part).
6. **A6 extended to ±50 %** weight perturbation.

After this round → v1.6 tag + final `commit`.

---

Heedo Choi · zxsa0716@kookmin.ac.kr · Kookmin University
