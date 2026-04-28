# PineSentry-Fire Data Acquisition Status

> 자동 갱신: `python scripts/integrity_check.py` 실행 후 `data/integrity_report.json`을 본 표에 반영.
> 진행 중인 task가 어디 있는지 사용자가 한눈에 파악.

## 현재 상태 (2026-04-26 D-127 시작 시점)

| # | 데이터셋 | 출처 | 인증 | 상태 | Hero 기여 |
|---|---|---|---|---|---|
| 1 | Tanager 5 forest scenes (NEON Bartlett·Niwot, Park Fire, Palisades, Tapajós) | Planet Open Data | Planet API key | ⏳ pending | 학습 set |
| 2 | EMIT 의성·산청 (Hero) + 광릉 + LA Palisades pre-fire | NASA EarthData | URS account | ⏳ pending — granule IDs 명시됨 (`scripts/search_emit_korea.py`) | **Hero 핵심** |
| 3 | Hyperion 광릉 2010-09-07 1 scene | USGS EarthExplorer | ERS account | ⏳ pending | 보너스 anchor |
| 4 | Sentinel-2 L2A baseline (10 ROI × 2 dates) | AWS Open Data | 무인증 | ⏳ pending | A1 ablation |
| 5 | GEDI L4A AGB Korea + 4 US sites | NASA EarthData | URS | ⏳ pending | 광역 검증 |
| 6 | NEON CFC + LMA + AOP (Bartlett, Niwot) | NEON | 무인증 | ⏳ pending | 학습 라벨 |
| 7 | TRY DB Korean *Pinus*/*Quercus* trait records | TRY | TRY MOU | ⏳ **신청 즉시** (4-6주) | PROSPECT prior |
| 8 | KoFlux GDK 18-mo EC | NCAM 포털 | 회원가입 | ⏳ pending | 광릉 sanity |
| 9 | 산림청 임상도 1:25,000 (8 ROI) | data.go.kr | 인증서 | ⏳ pending | disturbance 라벨 |
| 10 | 산불 perimeter (의성, 산청, 강릉, 울진) | data.go.kr / FFAS | 인증서 / MOU | ⏳ pending | **Hero ground truth** |
| 11 | MTBS US burn (LA Palisades, Park Fire, Bridge, Davis) | USGS | 무인증 | ⏳ pending | US 검증 |

## 사용 가능한 다운로드 스크립트

| 스크립트 | 데이터 | 명령 |
|---|---|---|
| `scripts/search_emit_korea.py` | EMIT 의성·산청 검증 | `python scripts/search_emit_korea.py` |
| `scripts/download_mtbs.py` | MTBS US 산불 perimeter | `python scripts/download_mtbs.py` |
| `scripts/download_s2.py` | Sentinel-2 baseline | `python scripts/download_s2.py` |
| `scripts/download_tanager.py` | Tanager STAC walk + 5 scene | `python scripts/download_tanager.py` |
| `scripts/download_neon.py` | NEON CFC/LMA/AOP | `python scripts/download_neon.py` |
| `scripts/download_gedi.py` | GEDI L4A | `python scripts/download_gedi.py` |
| `scripts/download_imsangdo.py` | 산림청 임상도 WFS | `python scripts/download_imsangdo.py` |
| `scripts/download_hyperion.py` | Hyperion 광릉 1 scene | `python scripts/download_hyperion.py` |
| `scripts/integrity_check.py` | 전체 무결성 점검 | `python scripts/integrity_check.py` |

## 7일 sequencing

- **D1 토** (4/26): MTBS + Sentinel-2 baseline (인증 불필요, 즉시)
- **D2 일** (4/27): EMIT 의성·산청 검색 + 다운로드 (EarthData 계정 필요)
- **D3 월** (4/28): Tanager STAC walk + scene 후보 확정 (Planet 계정 필요)
- **D4 화** (4/29): 산림청 임상도 + 산불 perimeter (data.go.kr 인증서 필요)
- **D5 수** (4/30): KoFlux GDK 데이터 수령 + Hyperion 광릉 (USGS ERS 필요)
- **D6 목** (5/1): NEON AOP HDF5 (대용량, 백그라운드)
- **D7 금** (5/2): GEDI L4A + 무결성 점검

## 막힘 시 폴백

| 막힘 | 폴백 |
|---|---|
| TRY DB 6주 지연 | NEON CFC labels만으로 PROSPECT prior |
| KoFlux 응답 늦음 | AsiaFlux DB (http://asiaflux.net) |
| FFAS perimeter 부재 | Sentinel-2 dNBR 자체 합성 |
| Tanager 한국 0건 | 30-scene wishlist 정당화 (변하지 않는 narrative) |
| Planet API 승인 지연 | Open Data Catalog 무인증 walk만 활용 |

이 STATUS.md를 매주 업데이트.
