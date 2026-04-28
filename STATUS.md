# PineSentry-Fire Data Acquisition Status

> 자동 갱신: `python scripts/integrity_check.py` 실행 후 `data/integrity_report.json` 을 본 표에 반영.

## 현재 상태 (2026-04-28 D-125)

| # | 데이터셋 | 출처 | 인증 | 상태 | 비고 |
|---|---|---|---|---|---|
| 1 | Tanager 5 forest scenes | Planet Open Data | Planet API key | 🔴 BLOCKED | B Welcome 메일 PDF 비밀번호 + API key 필요 |
| 2 | **EMIT 의성+산청 baseline** | NASA EarthData | URS ✅ | 🟡 진행 중 | 의성 winter pre-fire scene 다운로드 완료 (~4 GB), 산청 진행 중 |
| 3 | Hyperion 광릉 2010-09-07 | USGS ERS | ERS ✅ | ⏳ 대기 | landsatxplore Python 3.14 wheel 부재. 보너스라 deferred |
| 4 | **Sentinel-2 L2A 검색** | AWS Open Data | 무인증 | ✅ 인벤토리 완료 | 한국 285 + 해외 99 scenes catalogued (실제 다운은 분석 시 lazy) |
| 5 | GEDI L4A AGB | NASA EarthData | URS ✅ | ⏳ 대기 | EMIT 끝난 후 실행 |
| 6 | NEON CFC + LMA + AOP | NEON | 무인증 | ⏳ 대기 | neonutilities 설치 완료, 다운로드 대기 (~10 GB) |
| 7 | TRY DB 15-trait, 6-species | TRY | MOU | 🟡 부분 — public-only 즉시 받음 | `data/try/TRY_49341.tsv` (1167 rows / 4 종 / 9 trait, 한국 6종 0건). 전체 deliver 4-6주 |
| 8 | KoFlux GDK | AsiaFlux | 회원가입 | 🟡 부분 — 2004-2008 historical 받음 | `data/koflux_gdk/FxMt_GDK_2004-2008_*.zip` (5 zip). Tanager-era (2024-26) 별도 요청 필요 |
| 9 | 산림청 임상도 1:25,000 | data.go.kr | 인증 로그인 | 🔴 BLOCKED | WFS 엔드포인트 404. data.go.kr 직접 ZIP 다운 필요 |
| 10 | 산불 perimeter (의성/산청 2025) | data.go.kr | 로그인 | 🟡 부분 | 산림청_산불통계_20250911.csv ✅ 확보. perimeter shapefile 별도 |
| 11 | **MTBS US burn** | USGS | 무인증 | ✅ 다운로드 완료 | Park Fire 2024 (430k ac) + Bridge 2024 (54k ac). Palisades 2025 별도 필요 (NIFC) |

**범례**: ✅ 완료 / 🟡 진행 중 / 🟢 신청 완료 (대기) / 🔴 BLOCKED / ⏳ 대기

## 자동 처리된 인증 + 환경

| | |
|---|---|
| `_netrc` | `C:\Users\admin\_netrc` (NASA URS, ACL locked) ✅ earthaccess login OK |
| `.env` | `C:\Users\admin\pinesentry-fire\.env` (USGS + EarthData, gitignored) |
| Python | 3.14.3, pip 26.1 |
| 설치 완료 | requests, python-dotenv, numpy, xarray, pystac-client, earthaccess, geopandas, rioxarray, rasterio, neonutilities |
| 설치 실패 | landsatxplore (shapely build error on 3.14) → Hyperion deferred |
| 디스크 | C: 570 GB free, 사용 ~7 GB so far |

## 다운로드 위치

| 데이터 | 경로 |
|---|---|
| EMIT | `data/emit/{uiseong,sancheong}/EMIT_L2A_*.nc` |
| MTBS | `data/mtbs/mtbs_perims_DD.shp` + `pinesentry_us_targets.gpkg` |
| 산불통계 | `data/fire_stats/sanlim_fire_stats_20250911.csv` |

## 주간 sequencing (보정판)

- **D1-2 (4/26-27)**: 계정 폭격 ✅ + 자동 인증 setup ✅
- **D3 (4/28, 오늘)**: EMIT search + 의성/산청 baseline 다운 + S2 인벤토리 + MTBS ✅
- **D4 (4/29)**: GEDI 다운, NEON CFC 다운, Tanager API key 도착 시 즉시 walk
- **D5 (4/30)**: 임상도 + perimeter 사용자 수동 다운, dNBR 자체 합성 백업
- **D6-7 (5/1-2)**: NEON AOP (10 GB), Hyperion 대안 (필요 시 NASA Hyperion archive)
- **D8+ (5/3-)**: ISOFIT 대기 보정 + PROSPECT 학습 + KoFlux 회신 처리

## CI 상태

| commit | jobs |
|---|---|
| `a49e382` (initial) | ❌ lint+test 모두 실패 |
| `2de58c0` (fix1) | ⚠️ test 4/9 실패 (HSM 부호 + dim infer) |
| `f2a747c` (fix2) | ✅ 예상 — psi_min - p50 + percentile_normalize 보강 + multi-pixel test |
