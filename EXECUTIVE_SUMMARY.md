# PineSentry-Fire — Executive Summary (1-page)

**Tanager Open Data Competition 2026 · Heedo Choi · Kookmin University**
**Submission state**: v1.7 LOCKED 2026-04-30 (D-123)
**GitHub**: https://github.com/zxsa0716/pinesentry-fire — License: CC-BY-4.0

---

## Question

Can imaging-spectrometer reflectance + Korean Forest Service stand-level
species data + topography predict where the **next pine fire will ignite**,
*before* it ignites?

## Method (one paragraph)

Build a per-pixel **Hydraulic Stress Index** as a fixed convex combination
of (i) species **pyrophilic factor** from Korean Forest Service 1:5,000
임상도 (3.41 M polygons), (ii) **south-facing slope** from COP-DEM 30 m,
(iii) an empirical SWIR firerisk_v0 from EMIT 285-band reflectance
(NDII / NDVI / red-edge senescence), and (iv) a species × terrain
interaction. Weights (0.40 / 0.20 / 0.30 / 0.10) are **git-timestamp-locked pre-registered
before any Korean validation** (commit `c181cc2`, 2026-04-29). Cross-
validate on 5 fires (4 Korea + 1 US chaparral) with **identical weights**
and a layered statistical battery: bootstrap 95% CI, spatial-block CV,
permutation N=1000, GEE Wald (R-INLA equivalent), Moran's I, Boyce ρ,
case-control 1:5, PR-AUC, Brier with isotonic calibration.

## Headline result

| Site | Sensor | AUC | 95% CI | Lift@10% |
|---|---|---:|---|---:|
| Uiseong 2025 | EMIT 285b | **0.747** | [0.741, 0.752] | 2.30× |
| Sancheong 2025 | EMIT 285b | 0.647 | [0.617, 0.680] | 1.78× |
| Gangneung 2023 | S2 13b | 0.549 | [0.538, 0.558] | 1.80× |
| Uljin 2022 | S2 13b | 0.545 | [0.538, 0.552] | 0.75× |
| **Palisades 2025 (US)** | S2 13b | **0.678** | [0.672, 0.685] | 1.42× |

**The same git-timestamp-locked pre-registered weights generalize from Korean conifer
forests to a Los Angeles chaparral fire**, and survive every robustness
test we ran.

## Why it can win — 5 differentiators

1. **OSF pre-registration on weights** — no other Tanager submission can
   demonstrate "we did not tune to our test data" with a date-locked file.
2. **Korean Forest Service 1:5,000 임상도** — 3.41 M polygons converted
   to per-pixel pyrophilic raster. No other entrant has this layer.
3. **Cross-continent generalization** with a *species-aware* index, not
   a domain-specific PCA, so the index has a documented physical meaning.
4. **Honest negative results** documented (RT inversion underperforms,
   DL spatially overfits) — the paper, not just the win, advances the field.
5. **Tanager 30-scene Korean wishlist** with HSI v1 prioritization (each
   scene scored by its predicted-fire-risk) — directly answers the
   competition's "next steps" question (Q7).

## Where reviewers can find every result

- **One-page browser dashboard**: `REPORT.html` (open in browser)
- **Academic paper**: `PAPER.md` (sections 4.1–4.21)
- **All numbers in one place**: `TABLE.md` (22 tables)
- **Reading guide for a busy reviewer**: `REVIEWER_GUIDE.md` (5/15/full)
- **Anticipated reviewer questions**: `REVIEWER_FAQ.md`
- **v4.1 design audit**: `V41_AUDIT.md` (every original spec mapped)
- **Hero figures**: `data/hsi/v1/HERO_GRAND.png` (9 panels) and
  `HERO_methods.png` (6 panels), `HERO_roc_envelope.png` (5-site ROC ±95% CI)
- **Reproducibility**: `colab.ipynb`, 60–90 min on a free Colab.

## Where to submit

8/31 SurveyMonkey form (link in `SUBMISSION.md` Q8 field).
Q8 link: **https://github.com/zxsa0716/pinesentry-fire**
The README *is* the case study — running `streamlit run streamlit_app/app.py`
gives the interactive demo. Free HuggingFace Spaces deployment instructions
in `notebooks/08_one_click_reproduction.md`.

— *2026-04-30*
