# Master File Index — PineSentry-Fire

Comprehensive map of every artifact in the repository (and which are
local-only). Use this to find any file by category.

---

## 📄 Documentation (entry points)

| File | Audience | When to read |
|---|---|---|
| **`README.md`** | Everyone | First — repo entry, case study format |
| **`QUICKSTART.md`** | Cloners | If you just `git cloned` and want to run something |
| **`EXECUTIVE_SUMMARY.md`** | Reviewers (5 min) | Single-page brief, 5 differentiators |
| **`REVIEWER_GUIDE.md`** | Reviewers | Reading-path map: 5 / 15 / full |
| **`REVIEWER_FAQ.md`** | Reviewers | 10 anticipated questions + answers |
| **`SUBMISSION.md`** | Reviewers | The 8/31 form Q1–Q8 answers + headline numbers |
| **`PAPER.md`** | Deep readers | Academic writeup §1–§7 + 21 numbered results |
| **`TABLE.md`** | Deep readers | All 22 numerical tables in one place |
| **`V41_AUDIT.md`** | Deep readers | Original v4.1 design ↔ current state mapping |
| **`WEIGHTS_FREEZE.md`** | Verifiers | Weights + species priors locked at git `c181cc2` |
| **`CHANGELOG.md`** | Versioning | v1.0 → v1.9 history |
| **`STATUS.md`** | Auto-generated | Data inventory (765 files / 156 GB) |
| **`HUGGINGFACE_SPACES.md`** | Author / deployer | Step-by-step HF Space deployment guide |
| **`INDEX.md`** | Everyone | This file — master index |

---

## 🌐 Single-page artifacts

| File | Format | Size | What |
|---|---|---:|---|
| **`REPORT.html`** | self-contained HTML | 2.9 MB | All hero figures + 5 tables + 12-section narrative; opens in any browser, no install |
| **`colab.ipynb`** | Jupyter | tiny | 1-click Colab reproduction notebook |
| **`streamlit_app/app.py`** | Streamlit | tiny | 10-tab interactive demo (run locally or HF Space) |

---

## 🎨 `examples/figures/` — 16 visual outputs (committed!)

| # | File | Description |
|---:|---|---|
| 01 | `01_HERO_GRAND_9panel.png` | Top: Uiseong+Sancheong HSI maps + 5-site ROC. Mid: AUC bar + 2× lift charts. Bottom: 8-ROI peninsula atlas |
| 02 | `02_HERO_methods_6panel.png` | Method ladder, cross-site transfer, GEE OR + Moran I, permutation null, Boyce, per-species AUC |
| 03 | `03_HERO_roc_envelope_5site.png` | 5-site ROC with 95% bootstrap envelope (n=200) |
| 04 | `04_HERO_final_dual.png` | Original v1.0 dual-site Hero |
| 05 | `05_bootstrap_95CI.png` | 5-site AUC + lift bootstrap CIs |
| 06 | `06_permutation_null_N1000.png` | Null AUC distributions vs observed (N=1000) |
| 07 | `07_boyce_index.png` | Boyce continuous index curves |
| 08 | `08_A1_A4_ablations.png` | Component leave-one-out ΔAUC |
| 09 | `09_decisive_bands_285b.png` | Per-band AUC scan, decisive regions highlighted |
| 10 | `10_calibration_isotonic.png` | Reliability diagrams before/after isotonic |
| 11 | `11_PR_curves.png` | Precision-recall curves |
| 12 | `12_sensitivity_pm20pct.png` | A6 ±20% perturbation drift bars |
| 13 | `13_uiseong_eval.png` | Uiseong distribution + ROC + lift |
| 14 | `14_sancheong_eval.png` | Sancheong distribution + ROC + lift |
| 15 | `15_palisades_eval.png` | Palisades distribution + ROC + lift |
| 16 | `16_sancheong_temporal_T-1.5mo_animation.gif` | 3-frame multi-temporal pre-fire signal animation |

---

## 🗺 `examples/maps/` — Geographic outputs (committed!)

| File | Description |
|---|---|
| `korea_30_scene_wishlist.png` | Static map of 30 Tanager candidate scenes |
| `peninsula_8roi_atlas_montage.png` | 8-ROI HSI v1 atlas montage |

---

## 📊 `examples/tables/` — Every numerical result (committed!)

### Core results (5 sites)
- `bootstrap_5site_95CI.json` — AUC + lift mean/CI (n=200)
- `permutation_N1000.json` — observed vs null (p<1/1000 all 5 sites)
- `GEE_spatial_logit.json` — odds ratios + Wald
- `morans_I_spatial.json` — I(label) and I(residual)
- `boyce_continuous.json` — Boyce ρ
- `case_control_1to5.json` — Phillips-Elith 1:5 sampling
- `PR_AUC.json` — precision-recall area under
- `Brier_isotonic.json` — Brier raw vs isotonic-calibrated

### Ablations
- `A1_A4_leaveOneOut.json` — pyrophilic / south_facing / firerisk / pine_terrain drop-one
- `A1A2_tanager_VNIR_SWIR.json` — Tanager full vs VNIR vs SWIR vs S2-binned (Palisades)
- `uiseong_A6_pm20pct.json`, `_50pct.json` — A6 weight perturbation
- `sancheong_A6_pm50pct.json` — A6 ±50% Sancheong
- `cross_site_weight_transfer_OSF_defense.json` — Uiseong-fit weights → Sancheong loses 6.2 pts

### Trait inversion variants
- `v1_5_SMAP_integration.json` — HSI v1.5 with SMAP RZSM (Δ <0.002 AUC)
- `v2_5_PROSAIL_canopy.json` — PROSAIL canopy MLP (AUC 0.608)
- `v2_7_DiffPROSPECT_scipy.json` — scipy L-BFGS-B finite-diff (AUC 0.500, no signal)
- **`v2_8_DiffPROSPECT_torch.json`** — **PyTorch autograd (AUC 0.683)** ← v1.8 advance

### Other
- `koflux_NEE_dual_validation.json` — pooled 2006-2008 r=−0.117, p=5×10⁻¹³
- `decisive_bands_top30.json` — top 30 EMIT bands
- `DL_baseline_1DMLP.json` — random vs spatial-block DL baseline
- `ISOFIT_atmo_quality.json` — atmospheric residual flag fractions
- `per_species_auc.json` — within-cohort AUC per FRTP_NM
- `sancheong_multi_temporal.json` — T−15mo / T−1.5mo / T+3d
- `weather_baselines_KBDIFWIDWI_proxies.json` — RS-derived weather proxies
- `park_fire_2024.json` — MTBS Park Fire perimeter + reproduction recipe
- `roc_envelope_summary.json` — bootstrap ROC envelope summary
- `wishlist_30_scenes_priority.json` / `.csv` — 30 wishlist scenes ranked by HSI v1

---

## 💻 `src/pinesentry_fire/` — installable Python package

| File | Purpose |
|---|---|
| `__init__.py` | package init |
| `hsi.py` | `compute_hsm`, `hydraulic_stress_index`, `percentile_normalize` |
| `prospect_inversion.py` | PROSPECT-D forward + invert_one |

---

## 🧪 `tests/` — pytest 9/9 green

Run with `PYTHONPATH=src python -m pytest tests/`.

---

## 🔧 `scripts/` — 85 standalone reproduction scripts

### Build pipeline
- `build_hsi_v0.py` / `build_hsi_v1.py` / `build_hsi_v2.py` / `build_hsi_v2_5.py`
- `build_feature_stack.py` — 10-band per-pixel stack
- `build_hsi_v1_s2_fallback.py` — Sentinel-2 fallback for sites without EMIT
- `build_peninsula_atlas.py` — 8-ROI HSI atlas

### Trait inversion
- `train_prospect_mlp.py` — PROSPECT-D MLP (v2)
- `train_prosail_mlp.py` — PROSAIL canopy MLP (v2.5)
- `train_prospect_inversion.py` — older training script
- `prospect_inversion.py` — forward model (also in `src/`)
- `diff_prospect_inversion.py` — scipy L-BFGS-B (v2.7)
- `diff_prospect_torch.py` — **PyTorch autograd (v2.8)**

### Statistical battery
- `bootstrap_uncertainty.py` — 95% CI per site
- `permutation_test.py` / `permutation_test_n1000.py` — null distributions
- `spatial_block_cv.py` — 4×4 spatial block CV
- `spatial_logit_glmm.py` — GEE Wald (R-INLA equivalent)
- `morans_i.py` — spatial autocorrelation
- `boyce_index.py` — continuous Boyce
- `case_control_sampling.py` — Phillips-Elith 1:5
- `cross_site_weight_transfer.py` — OSF defense
- `precision_recall_calibration.py` — PR-AUC
- `isotonic_calibration.py` — Brier scores
- `hsi_sensitivity_analysis.py` / `hsi_sensitivity_50pct.py` — A6
- `run_ablations.py` — A1–A4 leave-one-out
- `decisive_bands_analysis.py` — per-band AUC scan
- `tanager_spectral_ablation.py` — A1+A2 VNIR vs SWIR
- `koflux_nee_validation.py` — dual-validation
- `multi_temporal_sancheong.py` — pre-fire signal
- `hsi_v1_5_smap.py` — SMAP integration
- `atmo_residual_check.py` — ISOFIT-equivalent
- `per_species_auc.py` — KFS cohort breakdown
- `dl_baseline_1dcnn.py` — DOFA stand-in
- `weather_baselines.py` — KBDI/FWI/DWI proxies

### Data download
- `run_all_downloads.py` — orchestrator
- `download_emit.py` / `download_emit_specific.py` / `search_emit_korea.py` / `search_more_emit_korea.py`
- `download_tanager.py` / `download_tanager_public.py` / `filter_and_download_tanager.py`
- `download_imsangdo.py` / `clip_imsangdo.py`
- `download_dem_copernicus.py` / `download_worldcover.py`
- `download_s2.py` / `download_sentinel1_sar.py`
- `download_gedi.py` / `download_smap_l4_sm.py` / `download_mod13q1_ndvi.py`
- `download_modis_fire.py` / `download_modis_fire_earthaccess.py`
- `download_mtbs.py` / `download_nifc_palisades.py`
- `download_neon.py` / `download_neon_cfc_only.py`
- `download_ecosis_spectra.py`
- `download_hyperion.py` / `extract_modis_fire_density.py` / `extract_smap_pre_fire.py`
- `vectorize_dnbr.py` / `synth_perimeter_dnbr.py`

### Visualization
- `make_grand_hero.py` — 9-panel hero
- `make_methods_comparison.py` — 6-panel methods
- `make_final_hero.py` — original dual hero
- `make_html_report.py` — REPORT.html
- `make_folium_map.py` — interactive map (folium)
- `make_temporal_gif.py` — multi-temporal animation
- `bootstrap_roc_envelope.py` — ROC ±95% CI bands
- `plot_5site_summary.py` — 5-site bootstrap chart
- `plot_sensitivity_robustness.py` — A6 chart
- `compute_spectral_baselines.py` / `compute_ndvi_anomaly.py`
- `evaluate_hsi_v0.py` — site evaluation
- `make_korea_wishlist.py` / `render_wishlist_map.py` — wishlist
- `wishlist_priority_score.py` — Q7 priority CSV

### Other
- `analyze_try.py` — TRY DB analysis
- `auto_update_status.py` — STATUS.md generator
- `integrity_check.py` — repo health
- `park_fire_2024_validation.py` — 6th-site framework

---

## 🎬 Demo entry points

| File | How to run |
|---|---|
| `streamlit_app/app.py` | `streamlit run streamlit_app/app.py` |
| `colab.ipynb` | Open in https://colab.research.google.com/github/zxsa0716/pinesentry-fire/blob/main/colab.ipynb |
| `Spacefile` | HuggingFace Spaces config (per `HUGGINGFACE_SPACES.md`) |
| `REPORT.html` | Double-click in any file browser |

---

## 🗂 `notebooks/` — supplementary notebooks

| File | Purpose |
|---|---|
| `08_one_click_reproduction.md` | Notes on Colab reproduction |
| (more notebooks may be added) | |

---

## 🌳 `wishlist/` — Q7 form artifacts

| File | Purpose |
|---|---|
| `korea_30_scenes.geojson` | 30 candidate Tanager scenes (Point + region + priority) |
| `korea_30_scenes.png` | Static map render |
| `korea_30_scenes_priority.csv` / `.json` | Ranked by predicted HSI v1 |
| `rationale.md` | Why these 30 scenes |

---

## 🗄 `.private/` — local-only (gitignored, not on GitHub)

| File | Reason hidden |
|---|---|
| `PROGRESS_REPORT.md` | Korean internal progress log |
| `SUBMISSION_CHECKLIST.md` | User's 8/31 admin to-do list |
| `REPORT_MAP.html` | 27 MB folium interactive map (too big for GitHub) |

---

## 📦 Raw data (`data/`, gitignored)

Not committed (765 files / 156 GB). See `STATUS.md` for the auto-
generated inventory and `data_playbook` notes for download recipes.

Layers:
- `emit/` — EMIT L2A reflectance (8 ROIs)
- `tanager/` — Tanager Open Data via STAC (Palisades 8 scenes)
- `s2_l2a/` — Sentinel-2 L2A
- `imsangdo/` — Korean Forest Service 1:5,000 (8 ROIs / 161K polygons)
- `dem/` — COP-DEM 30 m
- `worldcover/` — ESA WorldCover 10 m
- `gedi_l4a/` — GEDI L4A AGB (Korea + BART + NIWO)
- `mod13q1_ndvi/` — MOD13Q1 NDVI 16-day
- `smap_l4/` — SMAP L4 root-zone soil moisture
- `mtbs/` — MTBS US burn DB
- `fire_perimeter/` — dNBR perimeters
- `koflux_gdk/` — KoFlux GDK 2004–2008 CSVs
- `neon/` — NEON CFC + LMA
- `try/` — TRY DB public sample
- `tanager/` — Tanager Open Data
- `prospect/`, `features/`, `baselines/` — pipeline intermediates
- `hsi/v0/`, `hsi/v1/`, `hsi/v1_5/`, `hsi/v2/`, `hsi/v2_5/`, `hsi/v2_7/`, `hsi/v2_8/` — outputs by version
- `atlas/` — 8-ROI HSI atlas TIFs

---

*Generated 2026-05-04 at git tag `v1.9`.*
