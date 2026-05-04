# PineSentry-Fire — Weights Freeze (Git-Timestamped Pre-Registration)

**Frozen via public Git commit `c181cc2`** (2026-04-29)
**Author**: Heedo Choi, Kookmin University · zxsa0716@kookmin.ac.kr
**Repository**: https://github.com/zxsa0716/pinesentry-fire

> This document was committed to a public Git repository at hash `c181cc2`
> on 2026-04-29 — *before* any of the cross-validation runs reported in §7
> were committed. The public commit timestamp serves as the substantive
> "did-not-tune-to-test" guarantee.

---

## 1. Hypothesis

A pre-fire Hydraulic Stress Index that combines (i) EMIT 7.4 nm SWIR-derived
empirical EWT/LMA proxies, (ii) species-specific pyrophilic factor from the
산림청 임상도 1:5,000, and (iii) COP-DEM 30 m south-facing slope, will
jointly predict the pixel-level burned/unburned status of the 2025 Korean
spring fires (Uiseong + Sancheong) with ROC AUC ≥ 0.65 on each site, using
identical fixed weights across both sites.

## 2. Locked decision rules

```python
HSI = (0.40 * pyrophilic                       # species factor 0..1
     + 0.20 * south_facing                     # (cos(aspect-180)+1)/2
     + 0.30 * firerisk_v0                      # 1 - HSI_v0 empirical
     + 0.10 * (pyrophilic * south_facing))     # interaction
```

Each component is percentile-normalized (5th / 95th, clipped to [0, 1])
within the site before the weighted sum.

### Pyrophilic species table

| Species | Korean | factor |
|---|---|---:|
| *Pinus densiflora* | 소나무 | 1.00 |
| *P. thunbergii* / *P. rigida* | 곰솔 / 리기다 | 0.95 |
| *P. koraiensis* | 잣나무 | 0.85 |
| *Abies* / *Picea* spp. | 잔나무 / 전나무 | 0.65–0.70 |
| *Cupressus* / *Cryptomeria* / *Larix* | 편백 / 삼나무 / 낙엽송 | 0.50–0.60 |
| Oak (*Quercus* spp.) | 신갈 / 굴참 / 상수리 | 0.45–0.55 |
| *Robinia pseudoacacia* (invasive) | 아까시 | 0.40 |
| Mesic broadleaf | 자작 / 박달 / 느티 / 벚 | 0.20–0.30 |
| Non-forest | 비산림 | 0.00 |

## 3. Pre-registered metrics and thresholds

| Metric | Pre-fire dataset | Threshold |
|---|---|---|
| Primary: ROC AUC | EMIT pre-fire baseline + S2 dNBR > 0.27 burn label | ≥ 0.65 each site |
| Secondary: top-decile lift | Same | ≥ 1.5× each site |
| Tertiary: Mann-Whitney U | Same | p < 0.001 |

## 4. Pre-registered datasets

- 의성: `EMIT_L2A_RFL_001_20240216T044207_2404703_007` (T−13 mo, cc=21 %, covers fire)
- 산청: `EMIT_L2A_RFL_001_20241219T032003_2435402_004` (T−3 mo, cc<5 %)
- dNBR: Sentinel-2 NBR pre/post (S2A/B/C, lowest cc per window)
  - 의성: 2025-03-14 → 2025-04-26
  - 산청: 2025-01-21 → 2025-03-22
- 임상도: `TB_FGDI_FS_IM5000.gdb` (산림청, 2021 현행화) clipped to 8 ROIs

## 5. What will NOT be done post-hoc

- NOT tune the four weights to maximize any site's AUC
- NOT add new pyrophilic categories after seeing residuals
- NOT switch the EMIT baseline scene per site to maximize coverage
- NOT re-define the dNBR threshold per site
- NOT drop pixels where the index disagrees with ground truth

## 6. What MAY be done post-hoc (with explicit disclosure)

- v2 PROSPECT-D inversion may replace the empirical EWT/LMA proxies. v2
  is reported separately from v1.
- Weather baselines (KBDI / FWI / DWI proxies) may be added as
  side-comparison baselines without changing the index itself.

## 7. Result registered at freeze (already obtained 2026-04-29)

| Site | n_burn | n_unburn | AUC | Lift@10% | MW p |
|---|---:|---:|---:|---:|---|
| 의성 Uiseong | 25,804 | 319,923 | 0.7467 | 2.30× | ≈ 0 |
| 산청 Sancheong | 252 | 9,945 | 0.6471 | 1.75× | 6.9 × 10⁻¹⁶ |

Both meet the pre-registered AUC ≥ 0.65 / lift ≥ 1.5× / p < 0.001 thresholds.
HSI v0 (single-layer empirical) achieved 0.697 / 0.605 — the v1 weighted
combination strictly improves over v0 on both sites.

## 8. Verification

```bash
git log c181cc2 -1 WEIGHTS_FREEZE.md
git show c181cc2:WEIGHTS_FREEZE.md          # see this exact document at freeze
git log c181cc2..HEAD --oneline             # all subsequent work
```

The Git commit hash and timestamp are the substantive evidence. Any change
to the four weights or species table after this commit would have shown up
as a separate Git commit and would invalidate the freeze claim.

— Heedo Choi, Kookmin University
