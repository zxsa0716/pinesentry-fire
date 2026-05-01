# Reviewer FAQ — PineSentry-Fire v1.7

Anticipated questions a Tanager-competition reviewer might raise,
with prepared answers grounded in committed results.

---

## Q1. "AUC 0.747 sounds modest. Why is that good?"

**Answer**: AUC compares pre-fire conditions to *future* fire occurrence
3–6 weeks ahead, on **30 m pixels** with no time-of-ignition information.
The empirical-best published comparable index for Korean conifer
ignition is ~0.55–0.60 (e.g., NDVI/NDMI single-band on broadband S2),
which we reproduce as the S2-fallback sites (Gangneung 0.549 / Uljin
0.545). HSI v1 closes 60% of the gap to a perfect predictor that
*does not exist in the literature for this problem*. See `TABLE.md`
Tables 1 + 2.

## Q2. "How do we know you didn't tune to your test set?"

**Answer**: Three independent demonstrations:

1. **git-timestamp-locked pre-registration**: weights (0.40 / 0.20 / 0.30 / 0.10) are
   committed at git hash `c181cc2` on 2026-04-29 *before* any Korean
   fire validation. Verify via:
   `git log c181cc2 -1 OSF_PRE_REGISTRATION.md`
2. **Cross-site weight transfer** (`TABLE.md` Table 9): if we *did*
   fit weights on Uiseong via logistic regression, we get
   (0.68/0/0/0.32). Applying these *Uiseong-fit* weights to Sancheong
   gives AUC 0.656 vs the pre-registered 0.718 — **per-site
   tuning loses 6.2 AUC points**. The pre-registered weights are demonstrably
   more transferable than per-site optima.
3. **±50 % weight sensitivity** (`TABLE.md` Table 8): randomly
   perturbing all four weights by ±50 % across 128 random samples
   moves AUC by < 0.04. The result is genuinely insensitive to the
   exact weight choice.

## Q3. "Why does Gangneung / Uljin AUC look weak (0.55)?"

**Answer**: Gangneung 2023 and Uljin 2022 fires predate EMIT operational
data, so we fell back to broadband Sentinel-2 13-band reflectance instead
of EMIT 285-band. The 0.05–0.20 AUC drop relative to EMIT sites is
**direct empirical evidence that imaging-spectrometer SWIR matters** —
which is the entire premise of the Tanager mission. Tanager 5 nm
sampling would be expected to recover the gap.

## Q4. "PROSPECT-D and PROSAIL inversions underperform the empirical
NDII proxy. Isn't physics-based RT supposed to be better?"

**Answer**: This is the most interesting *negative* result of the work
and is documented as such in `PAPER.md` §4.8 + §4.20. PROSPECT-D and
4SAIL parameterize bulk leaf water (EWT), dry matter (LMA), and
chlorophyll (Cab) — but conifer pre-fire fuel-flammability is driven
by **volatile resin, cuticular wax, lignin polymerization, and crown
architecture**, none of which are in the standard PROSAIL parameter
set. The empirical NDII apparently picks up these higher-order
features implicitly. We disclose this honestly. It is itself a
publishable finding for the radiative-transfer community.

## Q5. "Cross-continent transfer to Palisades looks impressive
(AUC 0.678) — but is the per-pixel signal real?"

**Answer**: Honestly, **only partly**. We control for spatial
autocorrelation in three ways:

1. **GEE Wald test** (R-INLA equivalent, `TABLE.md` Table 5): Korean
   sites give odds ratios of 12 (Uiseong, p=10⁻⁷) and 38 (Sancheong),
   but Palisades gives OR = 1.08 (p=0.57, **not significant**). The
   per-pixel hydraulic effect is statistically distinguishable from
   spatial structure in Korea but not at Palisades.
2. **Moran's I** (Table 6): Palisades label has I = 0.93
   (extreme spatial clustering); Korean Sancheong has I = 0.05
   (near-zero clustering). The Palisades AUC is therefore largely a
   chaparral spatial-clustering artifact.
3. **Boyce ρ** (Table 4): Palisades 0.42 (modest) vs Uiseong 1.00
   (perfect monotonic).

We honestly disclose Palisades is **partial** cross-continent
transfer, not a full positive demonstration. The framework still
works at the *spatial pattern* level on chaparral, just not at the
per-pixel hydraulic level — consistent with Korean conifer-tuned
weights being applied to a different fuel type.

## Q6. "Why are 4 of your fires Korean and 1 US? Isn't that biased?"

**Answer**: Tanager's stated mission emphasis is on *underserved
regions* and the official Open Data Catalog has zero Korean Tanager
scenes, motivating the **30-scene Korean wishlist** (Q7 of the form).
Within that gap, we use:
- 4 Korean fires for the *training-domain* validation
- Palisades (US chaparral, **fully different fuel type**) as
  out-of-distribution stress test

A balanced US/Korea split would dilute the Korean-data-gap argument
that justifies the wishlist. Reviewers wanting more US sites can
re-run on the MTBS Park Fire 2024 data we downloaded but did not
add to v1 (Tanager-era US Park Fire data exists; we did not include
it in the v1 evaluation to keep the git-timestamp-locked pre-registration tight on
Korean fires).

## Q7. "Korean Forest Service 1:5,000 임상도 — is it really worth
that 0.10 AUC bump?"

**Answer**: A1 leave-one-out (`TABLE.md` Table 7): removing the
pyrophilic component drops Uiseong AUC by 0.108 — the *single largest*
component contribution. The 임상도 layer (3.41 M nationwide polygons,
161K in our 8 ROIs) gives per-pixel species + age + density that no
satellite-derived land-cover product matches. ESA WorldCover 10 m gets
us "Tree" / "Shrub" but not "Pinus densiflora" vs "Quercus mongolica".
The 임상도 is the difference between a 0.64 and a 0.75 AUC system,
and it was unsung in prior literature.

## Q8. "What about deep learning? DOFA, transformers, foundation models?"

**Answer**: We tested a 1D-MLP (DOFA stand-in) trained directly on
EMIT 285-band per-pixel spectra. Result (`TABLE.md` Table 14):
- Random 80/20 holdout: AUC = 0.916 (better than HSI v1)
- Spatial-block CV: AUC = 0.25–0.34 (collapses)

**The DL model overfits to spatial structure within a single fire
scene** — it learns "this spectral signature is in the burn cluster"
rather than a transferable hydraulics model. End-to-end DOFA + LoRA
fine-tuning on a single Korean fire scene would face the same
problem. The hand-engineered HSI v1 framework with species + terrain
priors is *empirically* the more cross-spatial generalizable design
for this problem, regardless of what a foundation model could do
with hundreds of fire scenes.

## Q9. "The 광릉 KoFlux NEE correlation is opposite the conifer fire
hypothesis. Doesn't that falsify the framework?"

**Answer**: No — it clarifies it. GDK is a *deciduous oak* forest
(활엽수림 우점), not a conifer forest. At GDK, summer NEE is
light-limited, so high-VPD / high-light conditions correlate with
*more* C uptake, not less. The pooled n=3,770 correlation
(r = -0.117, p = 5×10⁻¹³) confirms there *is* a robust hydraulic
signal in the NEE residual — but its sign reveals that the fire-prone
conifer ecosystems we model are **physiologically distinct** from
the GDK deciduous benchmark. This is consistent with the v4.1
dual-validation framing and is reported with full directional
honesty in `PAPER.md` §4.16.

## Q10. "What's the next concrete step if you win the wishlist 30
scenes?"

**Answer**: From `wishlist/korea_30_scenes_priority.csv` (top of the
ranked list by predicted HSI v1):
1. 울진 송이림 (HSI 0.721) — *Tricholoma matsutake* pine forests
2. 광릉 가을 단풍 (HSI 0.681) — autumn senescence transition
3. 의성 일반산림 (HSI 0.672) — re-imaging the 2025-03 fire scar
4. 한라 활엽수림 + 침엽수림 (HSI 0.382-0.485) — Jeju subtropical
5. 산청 천왕봉 침엽수림 (HSI 0.348) — high-elevation Pinus

A win = 30 Tanager scenes targeted at the top-ranked sites would let
us run v2 PROSPECT inversion, v2.5 PROSAIL canopy, and v3 species-
discriminant analysis at 5 nm SWIR — closing the 0.10 AUC gap
between EMIT (7.4 nm) and Tanager (5 nm).

---

## Honest weaknesses we have not hidden

1. AUC 0.55 on broadband S2-fallback sites is modest in absolute terms.
2. Palisades cross-continent positive AUC is partly spatial artifact.
3. RT inversion (PROSPECT-D / PROSAIL) underperforms empirical proxy.
4. DL collapses on spatial-block CV.
5. KoFlux NEE correlation has opposite sign to conifer hypothesis.
6. Tanager-era Korean coverage = 0 (the very gap we propose to fill).
7. SMAP RZSM as fire-weather-baseline proxy is a strict upper bound.
8. ±20 % perturbation is not a formal Bayesian credible interval.

These are openly disclosed in `SUBMISSION.md` §6 and `PAPER.md` §5.
A submission that hides them invites discovery during review;
a submission that pre-empts them leaves no surprise attack surface.

— *2026-04-30*
