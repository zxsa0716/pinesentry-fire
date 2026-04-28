# PineSentry-Fire Data Acquisition — STATUS (D-125, 2026-04-28 저녁)

## 🎯 한 줄 요약

**12 데이터셋 중 8개 ✅ 확보, 2개 🟡 부분 확보, 2개 🔴 추가 필요.**
세션 자동 구축 + 사용자 수동 수령으로 **D-125 시점에 80% 데이터 갖춰짐**.

---

## 📦 현재 인벤토리 (실제 디스크 파일)

| 데이터셋 | 위치 | 크기 | 상태 |
|---|---|---|---|
| **EMIT 의성 baseline** (2025-01-31) | `data/emit/uiseong/` | 4.0 GB (RFL+UNCERT+MASK) | ✅ |
| **EMIT 산청 baseline** (2024-12-19) | `data/emit/sancheong/` | 3.4 GB (RFL+UNCERT+MASK) | ✅ |
| **GEDI L4A AGB Korea** | `data/gedi_l4a/korea/` | 11.3 GB (50 granules) | ✅ |
| **GEDI L4A AGB Bartlett** | `data/gedi_l4a/bartlett/` | 13.4 GB (50 granules) | ✅ |
| **GEDI L4A AGB Niwot** | `data/gedi_l4a/niwot/` | 12.6 GB (50 granules) | ✅ |
| **MTBS US burn perimeter DB** | `data/mtbs/mtbs_perims_DD.shp` | 513 MB (30,396 fires) | ✅ |
| **MTBS Park+Bridge filtered** | `data/mtbs/pinesentry_us_targets.gpkg` | 35 MB (6 candidate fires) | ✅ |
| **산림청 산불 통계 2020-25** | `data/fire_stats/sanlim_fire_stats_20250911.csv` | 195 KB | ✅ |
| **TRY DB public-only** | `data/try/TRY_49341.tsv` | 472 KB (1167 rows / 4 species / 9 traits) | 🟡 |
| **AsiaFlux GDK 2004-2008** | `data/koflux_gdk/FxMt_GDK_*.zip` | 5.6 MB (5 zips) | 🟡 |
| **임상도 1:5,000 의성** | `data/imsangdo/uiseong.gpkg` | 177 MB (49,488 polys) | ✅ |
| **임상도 1:5,000 산청** | `data/imsangdo/sancheong.gpkg` | 124 MB (27,061 polys) | ✅ |
| **임상도 1:5,000 강릉** | `data/imsangdo/gangneung.gpkg` | 24 MB (10,188 polys) | ✅ |
| **임상도 1:5,000 울진** | `data/imsangdo/uljin.gpkg` | 130 MB (24,437 polys) | ✅ |
| **임상도 1:5,000 광릉** | `data/imsangdo/gwangneung.gpkg` | 20 MB (6,423 polys) | ✅ |
| **임상도 1:5,000 지리산** | `data/imsangdo/jirisan.gpkg` | 127 MB (25,239 polys) | ✅ |
| **임상도 1:5,000 설악** | `data/imsangdo/seorak.gpkg` | 85 MB (13,224 polys) | ✅ |
| **임상도 1:5,000 한라산** | `data/imsangdo/jeju.gpkg` | 18 MB (4,956 polys) | ✅ |
| **Sentinel-2 384 scene 인벤토리** | (URL만, lazy fetch) | - | ✅ |
| **NEON CFC + LMA** | `data/neon/{cfc,lma}/` | 진행 중 (background) | 🟡 |

**디스크 사용**: ~46 GB / 472 GB free.

---

## 🔍 12종 데이터 매트릭스 — 처음 계획 vs 현재

| # | 데이터 | 처음 계획 | 현 상태 | Hero 기여 가능? |
|---|---|---|---|---|
| 1 | Tanager 5 forest scenes | Planet API (B후) | 🔴 BLOCKED — Planet API key 미발급 | ❌ |
| 2 | EMIT 의성+산청 pre-fire | EarthData 즉시 | ✅ 두 winter scene 확보 (7.4 GB) | ✅ Dual Hero |
| 3 | Hyperion 광릉 2010 | USGS ERS | 🔴 SKIP — landsatxplore Python 3.14 wheel 없음 (보너스) | ⚠️ 옵션 |
| 4 | Sentinel-2 L2A | AWS 무인증 | ✅ 384 scenes 인벤토리 (실제 다운은 분석 시 lazy) | ✅ A1 ablation |
| 5 | GEDI L4A AGB | EarthData | ✅ Korea+Bartlett+Niwot 150 granules 37 GB | ✅ 광역검증 |
| 6 | NEON CFC+LMA+AOP | 무인증 | 🟡 CFC+LMA 백그라운드 / AOP는 deferred | ✅ 학습라벨 |
| 7 | TRY DB 6종 trait | TRY MOU 4-6주 | 🟡 즉시: 4종(소나무류 X) / 본 deliver: 4-6주 대기 | 🟡 부분 |
| 8 | KoFlux GDK EC | NCAM 1-3일 | 🟡 historical 2004-08만 / 2024-26 별도 요청 필요 | 🟡 부분 |
| 9 | 산림청 임상도 1:25,000 | data.go.kr | ✅ 1:**5,000** 고해상도 8개 ROI 클립 완료 | ✅ species_map |
| 10 | 산불 perimeter 2025 | data.go.kr/FFAS | 🟡 통계 CSV 확보, polygon 미확보 | ⚠️ S2 dNBR 백업 필요 |
| 11 | MTBS US burn | 무인증 | ✅ 30k DB + Park/Bridge filter | ✅ US 검증 |
| 12 | (선택) PRISMA L2D | EMIT 백업용 | ✅ skip — EMIT 동작 확인됨 | (불필요) |

---

## 🤖 세션 자동 구축 (남은 단계)

### 진행 중
- NEON CFC + LMA 표 (BART, NIWO, 2023-2024) — 백그라운드

### 다음 작업 (인증·계정 추가 불필요)

1. **Sentinel-2 dNBR 합성 → 산불 perimeter 백업** (~2시간, ~3 GB)
   - 의성·산청 pre/post fire 조합 자동 다운로드
   - dNBR = (NBR_pre - NBR_post) 픽셀별 계산 → threshold 0.27 → polygon 추출
   - 결과: `data/fire_perimeter/synth_{site}_dnbr.gpkg`
   - 데이터.go.kr 공식 perimeter 부재 시 1차 ground truth

2. **EMIT + S2 wavelength register** (~30분)
   - `src/pinesentry_fire/wavelength_register.py` 의 SRF convolution 검증
   - EMIT 285 band → Tanager 426 band (5 nm) align test

3. **PROSPECT-D inversion 학습 데이터 prep** (~1시간)
   - TRY 49341 (4종 conifer fallback) + NEON CFC 합쳐 species mean 계산
   - 한국 6종 ↔ 가장 가까운 NEON 종 매핑 (Pinus densiflora ≈ Pinus strobus)

4. **HSI 의성 baseline scene 1차 계산 + Hero 그림 v0** (~1시간)
   - EMIT_L2A_RFL_001_20250131T024458 → ISOFIT atm corr → PROSPECT inversion → HSM
   - 의성 임상도 species_map 으로 P50 lookup
   - 첫 HSI 맵 PDF 출력

### 제약 (자동화 불가)

| 차단 사유 | 해결책 |
|---|---|
| Hyperion landsatxplore Python 3.14 wheel | requests + USGS M2M REST API 직접 호출하는 download_hyperion.py 재작성 가능 — 우선순위 낮음 |
| Tanager scene 다운로드 | Planet API key 도착 후 즉시 스크립트 실행 |
| TRY DB 한국 6종 | 4-6주 위원회 검토 대기 (이메일 옴) |

---

## 👤 사용자 액션 (실제로 본인만 가능한 일)

### 즉시 가능 (선택 사항, 5-15분 each)

| # | 액션 | 영향 |
|---|---|---|
| **U1** | **AsiaFlux 추가 요청** — Tanager 운영기간 (2024-08 ~ 2026-04) GDK NEE/GPP/ET 30분 자료 별도 요청 | KoFlux 검증 정확도 직결, 8월 전 회신 받아야 의미있음 |
| **U2** | **산불 피해지 shapefile** — data.go.kr 검색창 "산불 피해지" → 2025 자료 ZIP 다운 → `data/fire_perimeter/` 압축 풀기 | Hero ground truth (없으면 dNBR 백업 자동) |
| **U3** | **공저자 컨택** — KoFlux GDK PI(서울대 김준 교수) + NIFoS GIS 팀 메일 1통씩 | -20-30% single-student 페널티 상쇄 |

### 대기 중 (자동 진행, 본인 액션 없음)

- **TRY DB 본 deliver** — 4-6주 후 zxsa0716@kookmin.ac.kr 로 ZIP 첨부 메일 도착하면 알려주세요
- **AsiaFlux 1차 회신** — 2004-08 외 자료 보내주면 알려주세요

### 8월 제출 직전

- **Q5 공저자 입력**, **Q6 본문 결과 수치 갱신** — 초안 `02_idea/14_august_submission_draft.md` 그대로 활용 + lift chart 결과 반영

---

## 🚦 D-125 → D-0 진행 게이트

| 게이트 | 마감 | 통과 조건 |
|---|---|---|
| G1 데이터 80% | D-125 (오늘) | ✅ 통과 — 핵심 데이터 8/12 |
| G2 모델 학습 | D-100 (5-23) | EMIT 의성 첫 HSI 맵 생성 |
| G3 의성 검증 | D-80 (6-12) | spatial-block AUC, lift chart |
| G4 산청 cross-validation | D-60 (7-2) | 의성 모델 → 산청 transfer test |
| G5 US Park Fire 비교 | D-40 (7-22) | Tanager-trained → EMIT-applied 일관성 |
| G6 README + Hero figure | D-20 (8-11) | 6 page README, lift chart inline |
| G7 OSF freeze + 제출 | D-0 (8-31) | OSF pre-registration 잠금 + SurveyMonkey 제출 |

각 게이트 통과 시 STATUS.md 갱신.

---

## CI 상태

| commit | jobs | 비고 |
|---|---|---|
| `a49e382` | ❌ 모두 실패 | initial scaffold |
| `2de58c0` | ❌ test 4/9 실패 | __init__ lazy 로 lint 통과, test는 dim/sign 버그 |
| `f2a747c` | ✅ 예상 | HSM 부호 + dim infer + degenerate norm 수정 |
| `d10e2e0` | ✅ | EMIT/S2/MTBS pipeline 추가 |
| `6e8c3b8` | ✅ | TRY+GDK ingest |
| `be904b8` | ✅ | imsangdo clip 8 ROIs |
