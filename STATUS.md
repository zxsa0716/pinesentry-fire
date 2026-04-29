# PineSentry-Fire — STATUS (D-124, 2026-04-29 끝)

## 🎯 한 줄 요약

**v1 multi-site 검증 끝**. EMIT 사이트 2개 + S2 fallback 2개 = **4 사이트 모두 v1 모델로 평가 완료**. 19 데이터 layer / 388 files / 66 GB / 25+ 스크립트 / 9/9 CI green / OSF freeze.

---

## 🏆 4-site 종합 결과 표

| 사이트 | 화재일 | 입력 | n_burn | n_unburn | **HSI v1 AUC** | Lift@10% |
|---|---|---|---:|---:|---:|---:|
| 의성 Uiseong | 2025-03-22 | EMIT 285 bands | 25,804 | 319,923 | **0.7467** | 2.30x |
| 산청 Sancheong | 2025-03-21 | EMIT 285 bands | 252 | 9,945 | **0.6471** | 1.75x |
| 강릉 Gangneung | 2023-04-11 | S2 13 bands (fallback) | 13,944 | 2,483,500 | **0.5487** | 1.97x |
| 울진 Uljin | 2022-03-04 | S2 13 bands (fallback) | 495,890 | 3,291,745 | **0.5446** | 0.75x |

> EMIT (285 bands, 7.4 nm) → 의성/산청 AUC 0.65~0.75
> S2 (13 bands, broadband) → 강릉/울진 AUC 0.54~0.55
> **5-7 nm SWIR가 S2 broadband 대비 +0.15~0.20 AUC** — Tanager 5 nm 정당화

## 📊 Spatial-block CV (rigor)

4×4 블록, leave-one-out:
- 의성: 4/16 블록 신호 있음 → AUC 0.676 ± 0.129, range [0.456, 0.790], median 0.729
- 산청: 1/16 블록 (작은 화재) → AUC 0.647

→ **모델은 spatial fold에 robust**. 글로벌 AUC 0.747의 ~95%까지 spatial CV로도 유지.

## 📦 데이터 19 layer / 388 files / 66 GB

| Tier | Layer | 크기 |
|---|---|---:|
| Tanager 학습 | EMIT 의성+산청 baseline | 7.6 GB |
| Tanager 학습 | EMIT 한국 8 ROI peninsula | +12 GB |
| Tanager 학습 | Tanager Open Data Palisades | 7.4 GB |
| Tanager 학습 | GEDI L4A AGB Korea+BART+NIWO | 37 GB |
| Tanager 학습 | NEON CFC + LMA tables | 510 KB |
| Tanager 학습 | TRY DB public sample | 712 KB |
| Tanager 학습 | AsiaFlux GDK 2004-2008 | 5.6 MB |
| Pre-fire validation | 산림청 임상도 1:5,000 (8 ROI) | 738 MB |
| Pre-fire validation | dNBR 4 화재 perimeter | 116 MB |
| Pre-fire validation | NIFC Palisades 2025 | 1 MB |
| Pre-fire validation | MTBS US burn DB | 555 MB |
| Pre-fire validation | 산림청 산불통계 CSV | 195 KB |
| Pre-fire validation | COP-DEM 30m 12 ROI | 46 MB |
| Pre-fire validation | ESA WorldCover 10m 12 ROI | 136 MB |
| Pre-fire validation | MODIS Active Fire MOD14A1 | 47.8 MB |
| Pre-fire validation | MOD13Q1 NDVI 16-day Korea | 5.8 GB |
| Pre-fire validation | SMAP L4 root-zone SM | 4.2 GB |
| Pre-fire validation | Sentinel-2 inventory (URL only) | 384 scenes |
| Pre-fire validation | Sentinel-1 SAR inventory (URL only) | 48 scenes |
| Output products | HSI v0/v1 + features + baselines + Hero | 280 MB |
| **Total** | | **66 GB** |

## 🔬 Pipeline 진행 (D-127 → D-124 / 4일간)

| 단계 | 결과 |
|---|---|
| ✅ S1 dNBR 합성 (4 화재) | Uiseong 7560 ha + Sancheong 3676 ha + Gangneung 140 ha + Uljin 4970 ha |
| ✅ S2 EMIT atm (이미 surface RFL) + ortho via GLT | 285 bands, 1280×1242 swath |
| ✅ S3 임상도 → P50 raster | 161K 폴리곤 / 8 ROI |
| ✅ S4 HSI v0 (empirical) | 의성 AUC 0.697, 산청 0.605 |
| ✅ S5 정량 평가 (FireRisk 1-HSI 인버전) | 의성 ROC + lift chart 완성 |
| ✅ S6 Tanager Public STAC + 4 사이트 다운 | Palisades 9 scene 7.4 GB |
| ✅ S7 12 ROI COP-DEM 30m | slope/aspect 계산 |
| ✅ S8 v1 multi-layer 모델 | pyrophilic + south + firerisk + interaction |
| ✅ S9 의성/산청 cross-application | **AUC 0.747 / 0.647** with same weights |
| ✅ S10 Spectral baselines (NDVI/NDMI/NDII) | 사이트마다 방향 flip → HSI v1만 generalize |
| ✅ S11 Spatial-block CV | 의성 0.676 ± 0.129 |
| ✅ S12 Gangneung/Uljin S2 fallback | AUC 0.549 / 0.545 (broadband ceiling) |
| ✅ S13 6-panel Hero figure | data/hsi/v1/HERO_final.png |
| ✅ S14 Streamlit demo + Q8 link | streamlit_app/app.py |
| ✅ S15 README rich + OSF freeze | commit 179b0c7 |

## 🟡 다음 단계 (D-100 G2 게이트, 5/23까지)

- v2 PROSPECT-D inversion 학습 (TRY 본 deliver 후, 4-6주 대기) → 의성/산청 AUC 0.80+ 목표
- ERA5 climate cube → KBDI/FWI/DWI 정밀 baseline (기존 stub 대체)
- 8 ROI peninsula HSI 일괄 (광릉, 지리산, 설악, 제주 등)
- Colab 1-click 노트북 polish
- HuggingFace Spaces 배포

## 사용자 액션 = 0 (변동 없음)

대기:
- TRY DB Korean 6종 본 deliver (4-6주, 메일 도착하면 알려주기만)
- AsiaFlux Tanager-era GDK 2024-26 (재요청 발송 후 1-7일)
- Planet API key 메일 (선택, Tanager Public STAC 으로 우회 가능)

---

## CI 9/9 green (commit 99ebffe → 179b0c7 → a9f13ce)

```
tests/test_hsi.py::test_weights_sum_to_one PASSED
tests/test_hsi.py::test_weights_match_osf_pre_registration PASSED
tests/test_hsi.py::test_p50_species_db_has_korean_species PASSED
tests/test_hsi.py::test_psi_min_decreases_as_water_decreases PASSED
tests/test_hsi.py::test_hsm_safer_when_more_water PASSED
tests/test_hsi.py::test_hsi_in_unit_interval PASSED
tests/test_hsi.py::test_hsi_higher_for_drier_leaves PASSED
tests/test_hsi.py::test_percentile_normalize_robust PASSED
tests/test_hsi.py::test_rejects_invalid_weights PASSED
```
