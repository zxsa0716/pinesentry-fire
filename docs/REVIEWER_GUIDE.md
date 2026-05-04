# Reviewer Guide — PineSentry-Fire

**Three reading paths depending on your time budget.**

---

## ⏱ 5-minute path (executive overview)

1. **`EXECUTIVE_SUMMARY.md`** — 1-page brief: question, method, headline result, 5 differentiators.
2. **`data/hsi/v1/HERO_GRAND.png`** — 9-panel hero figure: spatial maps (Uiseong + Sancheong) with burn perimeters, 5-site ROC, AUC bar, lift charts, 8-ROI peninsula atlas.
3. **`data/hsi/v1/HERO_roc_envelope.png`** — 5-site ROC with 95% bootstrap envelope (visualizes uncertainty as a SHAPE, not just a CI).

That's it. You now know what we did, what AUC we got, and how confident we are.

---

## ⏱ 15-minute path (informed reviewer)

After the 5-minute path, add:

4. **`SUBMISSION.md`** — 8/31 SurveyMonkey form fields Q1–Q8, plus full numerical results table, A1–A6 ablations, GEE / Moran I, cross-site weight transfer, and 8 limitations honestly disclosed.
5. **`data/hsi/v1/HERO_methods.png`** — 6-panel methods comparison: HSI v1 vs v0 vs v2 (PROSPECT) vs v2.5 (PROSAIL) vs DL random vs DL spatial, plus cross-site weight transfer + GEE OR + Moran I + Boyce + permutation null + per-species AUC. Designed so reviewers immediately see *every* finding at once.
6. **`WEIGHTS_FREEZE.md`** — locked at git commit `c181cc2` (2026-04-29). Verify via `git log c181cc2 -1 WEIGHTS_FREEZE.md` that the weight choices were committed BEFORE any Korean fire validation.
7. **`REVIEWER_FAQ.md`** — 10 anticipated reviewer questions with prepared answers.

---

## ⏱ Full reading path (deep reviewer)

After the 15-minute path, add:

8. **`PAPER.md`** — academic-style writeup, sections §1–§7 + 21 numbered results sections (4.1–4.21):
   - 4.1: 5-site main results
   - 4.2: spectral-baseline direction-flip finding
   - 4.3: permutation null
   - 4.4: Boyce continuous index
   - 4.5: GEE Wald spatial control
   - 4.6: A1–A4 leave-one-out
   - 4.7: A6 weight perturbation (±20% / ±50%)
   - 4.8: trait-inversion variants (v0 / v1 / v2 / v2.5 / v2.7)
   - 4.9: ISOFIT-equivalent atmosphere quality
   - 4.10: Moran's I diagnostic
   - 4.11: cross-site weight transfer (OSF defense)
   - 4.12: per-species breakdown
   - 4.13: 1D-MLP DOFA stand-in
   - 4.14: multi-temporal pre-fire signal (Sancheong T-1.5mo)
   - 4.15: SMAP RZSM integration (HSI v1.5)
   - 4.16: KoFlux GDK NEE residual dual-validation
   - 4.17: Tanager spectral subset ablation (A1+A2)
   - 4.18: case-control 1:5 sampling
   - 4.19: weather-only baselines (KBDI/FWI/DWI proxies)
   - 4.20: DiffPROSAIL gradient inversion (A3)
   - 4.21: deferred items (DOFA + LoRA, formal abandonment)
9. **`TABLE.md`** — 22 tables consolidating every numerical result on one page.
10. **`V41_AUDIT.md`** — original v4.1 design (2026-04-26) mapped element-by-element to current state (✅ done / 🟡 substituted / ⏸ abandoned with rationale).
11. **`PROGRESS_REPORT.md`** — Korean-language comprehensive briefing.
12. **`CHANGELOG.md`** — version history v1.0 → v1.7.

---

## Reproducibility (≈ 90 minutes total wall time on free Colab)

```bash
git clone https://github.com/zxsa0716/pinesentry-fire.git
cd pinesentry-fire
pip install -r requirements.txt
python -c "import earthaccess; earthaccess.login(persist=True)"  # NASA URS

python scripts/run_all_downloads.py            # ~60 GB, 8 layers
python scripts/build_hsi_v0.py uiseong         # AUC 0.697 in ~5 min
python scripts/build_feature_stack.py uiseong  # 10-band stack
python scripts/build_hsi_v1.py uiseong         # AUC 0.747
python scripts/make_grand_hero.py              # 9-panel hero

python scripts/permutation_test_n1000.py       # 5-site p < 1/1000
python scripts/spatial_logit_glmm.py           # GEE Wald
python scripts/morans_i.py                     # Moran's I
python scripts/case_control_sampling.py        # 1:5 sampling
python scripts/hsi_sensitivity_50pct.py        # ±50% perturbation
python scripts/cross_site_weight_transfer.py   # OSF defense
python scripts/koflux_nee_validation.py        # NEE dual-validation
python scripts/tanager_spectral_ablation.py    # A1+A2
python scripts/diff_prospect_inversion.py      # A3
python scripts/bootstrap_roc_envelope.py       # 5-site ROC ±95% CI
python scripts/wishlist_priority_score.py      # Q7 prioritization

PYTHONPATH=src pytest tests/ -v                # 9/9 green
streamlit run streamlit_app/app.py             # interactive demo
```

Every metric in `TABLE.md` corresponds to a script + a JSON output.

---

## Key data inputs (for reviewers verifying claims)

| Layer | Source | Path |
|---|---|---|
| EMIT L2A reflectance | NASA / JPL via earthaccess | `data/emit/{site}/EMIT_L2A_RFL_*.nc` |
| Korean Forest Service 임상도 1:5,000 | data.go.kr `3045619` | `data/imsangdo/{site}.gpkg` (clipped) |
| COP-DEM 30 m | ESA via opentopography | `data/dem/{site}_dem.tif` |
| dNBR perimeters | Sentinel-2 NBR pre-post threshold > 0.27 | `data/fire_perimeter/synth_{site}_dnbr.gpkg` |
| NIFC Palisades 2025 | NIFC authoritative | `data/fire_perimeter/nifc_palisades_2025.geojson` |
| Tanager 8 Palisades scenes | Planet Open Data STAC | `data/tanager/palisades/` |
| KoFlux GDK 2004–2008 | AsiaFlux portal | `data/koflux_gdk/FxMt_GDK_*.zip` |

---

## Single-page browser dashboard

Open **`REPORT.html`** in any browser for a scrollable view of all hero
figures + key tables + narrative — no install required.

— *Heedo Choi · zxsa0716@kookmin.ac.kr · Kookmin University*
