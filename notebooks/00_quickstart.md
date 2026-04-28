# PineSentry-Fire — 노트북 7개 빠른 시작 가이드

> Final v4.1 design (locked 2026-04-26). 16-week schedule.

## 노트북 매핑 (Hero figure에 어떻게 기여하는가)

| Notebook | Week | Output | Hero figure 기여 |
|---|---|---|---|
| `01_setup_inventory.ipynb` | 0-1 | STAC inventory, 5 scene 후보, EMIT scene IDs | 인프라 |
| `02_isofit_atmcorr.ipynb` | 1-2 | Surface reflectance for all scenes | 인프라 |
| `03_engine_training.ipynb` | 3-6 | DOFA + LoRA + DiffPROSAIL trained ckpt | 모델 |
| `04_us_palisades_validation.ipynb` | 7 | LA Palisades pre-fire HSI + AUC | F4 |
| `05_uiseong_sancheong_dual_hero.ipynb` | 8-9 | **★ Hero figure 1차** | **F5 Hero** |
| `06_gwangneung_koflux_check.ipynb` | 10 | EMIT-derived HSI vs KoFlux NEE 시계열 | F6 |
| `07_korea_pre_fire_atlas.ipynb` | 11 | 한반도 동해안 HSI 지도 + 30-scene wishlist GeoJSON | F7 |

## 실행 순서

### Week 0 (오늘부터)
```bash
conda env create -f env/environment.yml
conda activate pinesentry-fire

# Day 2: EMIT critical-path 검증
python scripts/search_emit_korea.py
```

### Week 1-2: 데이터 확보
- Tanager 5 글로벌 forest scene
- EMIT 의성 + 산청 (Hero) + 광릉 (sanity)
- Sentinel-2 baseline 7 ROI
- Hyperion 광릉 2010-09-07 (보너스)
- NEON CFC/LMA + AOP 타일

### Week 3-6: 모델 학습
- ISOFIT atmospheric correction
- DOFA + LoRA + Wavelength-Prompt Token 학습
- DiffPROSAIL dual-branch reconstruction loss
- HSI는 physiological prior 고정 (절대 학습하지 않음)
- Pre-register HSI weights on OSF before validation

### Week 7-9: Hero 검증
- LA Palisades 2025-01 pre-fire (US)
- 의성 2025-03 + 산청 2025-03 pre-fire (Korea, Dual Hero)
- Spatial logistic GLMM + permutation test
- Baseline 5종 (DWI, FWI, KBDI, NDMI, NDVI) 동시 ROC

### Week 10-12: 보조 분석 + 운영
- KoFlux NEE × HSI 시계열 (sanity)
- 한반도 pre-fire HSI atlas
- 30-scene wishlist GeoJSON

### Week 13-15: 광택 (양보 불가)
- Hero figure Figma 마감
- Streamlit + HuggingFace Spaces deploy
- README 6 page final
- Colab 1-click 동작 확인

### Week 16: 제출
- 8/24 1차
- 8/31 final

## 디렉토리 가이드

```
pinesentry-fire/
├── README.md           ← 이게 곧 case study (별도 paper 없음)
├── env/                ← conda env
├── scripts/            ← 데이터 다운로드 자동화
├── src/pinesentry_fire/ ← 핵심 라이브러리 (HSI, traits)
├── notebooks/          ← 7개 노트북
├── streamlit_app/      ← 인터랙티브 데모
├── wishlist/           ← 30-scene 정당화 + GeoJSON
├── tests/              ← pytest
└── colab.ipynb         ← 1-click 재현
```

## 자주 막히는 곳

| 지점 | 막힘 신호 | 폴백 |
|---|---|---|
| ISOFIT 셋업 | Docker GPU 의존성 | 6SV + Planet L2A 직접 사용 |
| DOFA weight 로드 | terratorch issue | HuggingFace Hub 직접 |
| DiffPROSAIL autograd | gradient stability | LUT-NN surrogate |
| EMIT 의성 다운로드 | EarthData 인증 | `~/.netrc` 수동 |
| KoFlux 데이터 지연 | NCAM 응답 | AsiaFlux DB 백업 |

각 막힘은 `02_idea/05_backup_recommendations.md` 의사결정 트리 참조.
