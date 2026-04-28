# PineSentry-Fire

> Tanager-trained Hydraulic Stress Index for predicting Korean *Pinus densiflora* fire ignition.
> Submission to Planet Tanager Open Data Competition 2026 (deadline 2026-08-31).

[![Colab](https://img.shields.io/badge/Colab-1--click-orange)](https://colab.research.google.com)
[![License](https://img.shields.io/badge/License-CC--BY--4.0-blue)](LICENSE)
[![DOI](https://img.shields.io/badge/Zenodo-pending-lightgrey)](#)

---

## Hero Figure (placeholder — populated by Week 13-15)

> *"Pre-fire Hydraulic Stress Index identifies 의성·산청 2025 burn footprints at AUC 0.XX (lift = X.Xx in top decile), outperforming weather-only baselines."*

[Hero figure here — see `notebooks/05_hero_figure.ipynb`]

---

## ONE question

**Can Tanager 5 nm × SWIR hyperspectral measurements jointly explain (a) 광릉 KoFlux eddy-covariance NEE residuals AND (b) 의성·산청 2025 ignition susceptibility — outperforming weather-only baselines (DWI, FWI, KBDI)?**

## Method (10-step logic chain)

1. Eastern-coast pine fire frequency rising (산림청 stakeholder, urgency).
2. Anderegg 2020 *Science*: leaf hydraulic decline precedes mortality/ignition by 1-3 yr.
3. Sentinel-2 13-band cannot resolve the leaf-N · EWT signature (ablation A1).
4. Tanager 5 nm × SWIR (1510, 970, 2080 nm) can (ablation A2).
5. Train trait engine on 5 global Tanager forest scenes with NEON AOP labels.
6. Combine 5 traits into Hydraulic Stress Index (HSI) using physiological prior (hydraulic safety margin, Martin-StPaul 2017 *Ecol. Lett.*).
7. Validate on LA Palisades 2025-01 (Tanager 5-month pre-fire window).
8. Transfer to EMIT (60 m × 285 bd) for Korea: Uiseong + Sancheong 2025-03 fires.
9. Sanity check: EMIT-derived HSI time series vs KoFlux GDK NEE (광릉, 1996-2026).
10. Korea east-coast pre-fire HSI atlas + 30-scene Tanager wishlist for 30 m × 5 nm precision upgrade.

## Architecture

```
Tanager L1B → ISOFIT atm corr → Surface Reflectance (BOA)
   ↓
DOFA backbone (frozen, wavelength-conditioned ViT)
   + Wavelength-Prompt Token (λ → sin/cos)
   + single LoRA rank-16 adapter
   ↓
Trait head: 5 channels (LMA, EWT, N, lignin, REIP)
   ↓
DiffPROSAIL/4SAIL2 dual-branch (PyTorch autograd) → reconstruction loss
   ↓
HSI = w_safety·(1−HSM) + w_water·(1−EWT_norm) + w_starch·LMA_norm
   ↓
Spatial logistic GLMM (R-INLA) on burn perimeter
```

## Validation

- **Tier-1 (open)**: GEDI L4A AGB, 산림청 임상도 1:25,000, 산림청 산불 GIS perimeter
- **Tier-2 (request)**: KoFlux GDK 광릉 18-mo EC (NCAM portal), TRY DB Korean *Pinus*/*Quercus* (4-6 weeks)
- **US benchmark**: NEON AOP CFC/LMA + MTBS LA Palisades perimeter
- **Cross-sensor**: Hyperion 광릉 2010-09-07 (Park et al. 2019 ISPRS IJGI 8(3):150) bonus anchor

## Ablations (6 + sensitivity)

| # | Ablation | Hypothesis |
|---|---|---|
| A1 | Sentinel-2 binned vs Tanager full | H1 (Tanager-decisive) |
| A2 | Tanager full vs SWIR-only vs VNIR-only | H1 |
| A3 | DiffPROSAIL on/off | OOD generalization |
| A4 | Single-mission vs EMIT cross-sensor transfer | H2 |
| A5 | HSI vs DWI / FWI / KBDI / NDMI / NDVI baselines | H3 (outperformance) |
| A6 | HSI weight ±50% sensitivity | Robustness |

## Reproducibility

- Conda env: `env/environment.yml`
- Colab 1-click: `colab.ipynb`
- Docker: `pinesentry-fire:v4.1`
- Streamlit demo: HuggingFace Spaces (URL pending)
- Pre-registered design: OSF (URL pending)
- Zenodo DOI: pending Week 14

## 30-Scene Korean Wishlist (Tanager Open Data Competition prize)

| Group | Sites | Scenes |
|---|---|---|
| A. 광릉 KoFlux super-site | GDK + CFK | 8 |
| B. 백두대간 conifer ridges | 점봉·지리·덕유·설악 | 6 |
| C. East-coast fire chronosequence | 의성·울진·강릉 | 6 |
| D. 동해안 송이 *P. densiflora* | 봉화·울진 | 4 |
| E. DMZ uncontrolled reference | 강원·경기 DMZ | 3 |
| F. 한라산 elevation gradient | 1100–1950 m | 3 |
| **Total** | | **30** |

Downstream users: 산림청 산불대응센터 / 기상청 AsiaFire / IPCC AR7 East Asia regional synthesis.
See `wishlist/rationale.md` and `wishlist/korea_30_scenes.geojson`.

## Citation

```
@misc{pinesentry-fire-2026,
  author = {},
  title  = {PineSentry-Fire: Tanager-trained Hydraulic Stress Index for Korean Pine Fire Prediction},
  year   = {2026},
  note   = {Planet Tanager Open Data Competition 2026 Submission},
  doi    = {pending}
}
```

(Author/co-author fields filled at submission time.)

## License

CC-BY-4.0 (compatible with Tanager Open Data CC-BY).

## Acknowledgements

- Planet Labs PBC — Tanager Open Data Catalog
- NASA JPL — EMIT mission
- USGS / NASA — GEDI, Hyperion archives
- 산림청 / 국립산림과학원 — 임상도 + 산불 GIS
- KoFlux / NCAM — Gwangneung GDK eddy-covariance
- TRY Plant Trait Database
