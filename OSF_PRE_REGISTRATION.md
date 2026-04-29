# PineSentry-Fire OSF Pre-Registration

**Frozen**: 2026-04-29 (D-124, before any further hyperparameter changes)
**Author**: Heedo Choi (Kookmin University, zxsa0716@kookmin.ac.kr)
**Repo at freeze**: `c181cc2` (https://github.com/zxsa0716/pinesentry-fire)

---

## 1. Hypothesis

A pre-fire Hydraulic Stress Index that combines (i) EMIT 7.4 nm SWIR-derived
empirical EWT/LMA proxies, (ii) species-specific pyrophilic factor from the
산림청 임상도 1:5,000, and (iii) COP-DEM 30m south-facing slope, will jointly
predict the pixel-level burned/unburned status of the 2025 Korean spring
fires (Uiseong + Sancheong) with ROC AUC >= 0.65 on each site, using
identical fixed weights across both sites.

## 2. Locked decision rules

```python
HSI_v1 = (0.40 * pyrophilic                         # species factor 0..1
        + 0.20 * south_facing                       # (cos(aspect-180)+1)/2
        + 0.30 * firerisk_v0                        # 1 - HSI_v0 empirical
        + 0.10 * (pyrophilic * south_facing))       # interaction
```

Each component is percentile-normalized (5th / 95th, clipped to [0,1])
within the site before the weighted sum.

| Pyrophilic species table | factor |
|---|---:|
| 소나무 Pinus densiflora | 1.00 |
| 리기다소나무 / 곰솔 | 0.95 |
| 잣나무 Pinus koraiensis | 0.85 |
| 잔나무 / 전나무 | 0.65–0.70 |
| 편백 / 삼나무 / 비자 / 낙엽송 | 0.50–0.60 |
| 신갈 / 굴참 / 상수리 등 oaks | 0.45–0.55 |
| 자작 / 박달 / 밤 / 물푸레 / 서어 / 느티 / 벚 등 mesic broadleaf | 0.20–0.30 |
| 아까시 (invasive) | 0.40 |
| 비산림 (경작지/주거지/수체/과수원/제지 등) | 0.00 |

## 3. Pre-registered metrics

| Metric | Pre-fire dataset | Threshold |
|---|---|---|
| Primary: ROC AUC | EMIT pre-fire baseline + S2 dNBR > 0.27 burn label | >= 0.65 each site |
| Secondary: top-decile lift | Same | >= 1.5x each site |
| Tertiary: Mann-Whitney U | Same | p < 0.001 |

## 4. Pre-registered datasets

- 의성: EMIT_L2A_RFL_001_20240216T044207_2404703_007 (T-13 mo, cc=21%, covers fire)
- 산청: EMIT_L2A_RFL_001_20241219T032003_2435402_004 (T-3 mo, cc<5%)
- dNBR: Sentinel-2 NBR pre/post (S2A/B/C, lowest cc per window)
  - 의성: 2025-03-14 -> 2025-04-26
  - 산청: 2025-01-21 -> 2025-03-22
- 임상도: TB_FGDI_FS_IM5000.gdb (산림청, 2021 현행화) clipped to 8 ROIs

## 5. What we will NOT do post-hoc

- NOT tune the four weights to maximize Uiseong AUC.
- NOT add new pyrophilic categories after seeing Sancheong residuals.
- NOT switch the EMIT baseline scene per site to maximize coverage.
- NOT re-define the dNBR threshold per site.
- NOT drop pixels where HSI v1 disagrees with ground truth.

## 6. What we MAY do post-hoc (only if disclosed in the writeup)

- v2 PROSPECT-D inversion may replace empirical EWT/LMA proxies once
  TRY DB Korean species delivery arrives (~6 weeks). v2 will be reported
  separately from v1 and will require its own pre-registration.
- ERA5 climate baselines (KBDI/FWI/DWI) may be added when the climate cube is
  on disk — these are addition baselines, not changes to HSI v1 itself.

## 7. Result registered at freeze (already obtained 2026-04-29)

| Site | n_burn | n_unburn | AUC | Lift@10% | MW p |
|---|---:|---:|---:|---:|---|
| 의성 Uiseong | 25,804 | 319,923 | 0.7467 | 2.30x | ~0 |
| 산청 Sancheong | 252 | 9,945 | 0.6471 | 1.75x | 6.9e-16 |

Both meet the pre-registered >= 0.65 / >= 1.5x / p<0.001 thresholds.
HSI v0 (single-layer empirical) was 0.6970 / 0.6047 — v1 strictly improves.

## 8. Code commit hash at freeze

`c181cc2` — `git show c181cc2`. Subsequent commits (Hero figure, README, this
document, OSF posting) do NOT alter the model formula or weights.

— Heedo Choi, 2026-04-29
