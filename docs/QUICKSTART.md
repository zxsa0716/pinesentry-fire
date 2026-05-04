# PineSentry-Fire — QUICKSTART

**Tanager Open Data Competition 2026 · Heedo Choi · Kookmin University**
**License**: CC-BY-4.0 · **GitHub**: https://github.com/zxsa0716/pinesentry-fire

---

## 0 — TL;DR

```bash
git clone https://github.com/zxsa0716/pinesentry-fire.git
cd pinesentry-fire
pip install -r requirements.txt
PYTHONPATH=src python -m pytest tests/   # 9/9 should pass
streamlit run streamlit_app/app.py        # interactive demo, browser opens
```

That's enough to see every result this submission produces. The repo
ships with `examples/` containing all key figures + JSON tables, so the
streamlit app and the colab notebook work without re-running the pipeline.

---

## 1 — What you can do in 5 minutes (no compute)

| Action | Where |
|---|---|
| 📖 Read 1-page brief | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) |
| 🎨 See the 9-panel hero | [`examples/figures/01_HERO_GRAND_9panel.png`](../examples/figures/01_HERO_GRAND_9panel.png) |
| 📊 Browse all 22 result tables | [`TABLE.md`](TABLE.md) |
| 🌐 Open the browser dashboard | Open [`REPORT.html`](REPORT.html) in any browser |
| 🎬 Watch pre-fire signal animation | [`examples/figures/16_sancheong_temporal_T-1.5mo_animation.gif`](../examples/figures/16_sancheong_temporal_T-1.5mo_animation.gif) |
| ❓ Read FAQ | [`REVIEWER_FAQ.md`](REVIEWER_FAQ.md) |

---

## 2 — Run the interactive demo (1 minute)

```bash
pip install streamlit
streamlit run streamlit_app/app.py
```

This opens a browser tab with **10 tabs**: Overview, Hero figures,
5-site results, Methodology, Statistical battery, Trait inversion,
Dual-validation, Pre-fire temporal, Q7 wishlist, Reproducibility.

The app reads from `examples/` so it works on a clean clone with no
data download.

---

## 3 — 1-click Colab reproduction (90 minutes)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zxsa0716/pinesentry-fire/blob/main/colab.ipynb)

The notebook walks through:
1. Setup (3 min)
2. View pre-computed examples (no compute)
3. Sanity-check pytest (1 min)
4. (Optional) Full pipeline — download EMIT + 임상도 + DEM + dNBR perimeters and rebuild HSI v1 (60–90 min, ~60 GB downloads)
5. Inspect every output figure inline

---

## 4 — Local full pipeline reproduction (~90 minutes)

Requires NASA Earthdata account (free at https://urs.earthdata.nasa.gov):

```bash
pip install -r requirements.txt
python -c "import earthaccess; earthaccess.login(persist=True)"

python scripts/run_all_downloads.py            # ~60 GB across 8 layers
python scripts/build_hsi_v0.py uiseong         # AUC 0.697
python scripts/build_feature_stack.py uiseong  # 10-band stack
python scripts/build_hsi_v1.py uiseong         # AUC 0.747
python scripts/make_grand_hero.py              # rebuild HERO_GRAND.png
```

Then run any of the analysis scripts:

```bash
python scripts/bootstrap_uncertainty.py        # → bootstrap_5site_95CI.json
python scripts/permutation_test_n1000.py       # 5-site p < 1/1000
python scripts/spatial_logit_glmm.py           # GEE Wald
python scripts/morans_i.py                     # Moran's I
python scripts/case_control_sampling.py        # Phillips-Elith 1:5
python scripts/diff_prospect_torch.py          # PyTorch autograd PROSPECT-D
python scripts/koflux_nee_validation.py        # NEE dual-validation
python scripts/tanager_spectral_ablation.py    # A1+A2 (Palisades)
python scripts/wishlist_priority_score.py      # Q7 priority CSV
python scripts/make_html_report.py             # rebuild REPORT.html
```

---

## 5 — Repository layout

```
pinesentry-fire/
├── README.md                  ← entry point (case study)
├── QUICKSTART.md              ← this file
├── EXECUTIVE_SUMMARY.md       ← 1-page brief
├── REVIEWER_GUIDE.md          ← 5/15/full reading paths
├── REVIEWER_FAQ.md            ← 10 anticipated questions + answers
├── HUGGINGFACE_SPACES.md      ← live demo deployment guide
├── INDEX.md                   ← master file map
├── PAPER.md                   ← academic writeup (4.1-4.21)
├── TABLE.md                   ← 22 numerical tables
├── V41_AUDIT.md               ← v4.1 design compliance audit
├── WEIGHTS_FREEZE.md    ← git-timestamp-locked weights
├── SUBMISSION.md              ← 8/31 SurveyMonkey form fields
├── CHANGELOG.md               ← v1.0 → v1.9 history
├── STATUS.md                  ← auto-generated data inventory
├── REPORT.html                ← single-page browser dashboard (2.9 MB)
├── colab.ipynb                ← 1-click Colab pipeline
├── streamlit_app/app.py       ← interactive demo
├── Spacefile                  ← HuggingFace Spaces config
├── requirements.txt           ← Python deps
├── pyproject.toml             ← package metadata
├── LICENSE                    ← CC-BY-4.0
├── CITATION.cff               ← citation metadata
│
├── src/pinesentry_fire/       ← installable package
│   ├── hsi.py                 ← HSI computation
│   ├── prospect_inversion.py  ← PROSPECT-D forward
│   └── ...
├── tests/                     ← pytest 9/9 green
│
├── scripts/                   ← 85 standalone reproduction scripts
│   ├── build_hsi_v0.py / v1.py / v2.py / v2_5.py
│   ├── train_prospect_mlp.py / train_prosail_mlp.py
│   ├── diff_prospect_torch.py ← PyTorch autograd
│   ├── bootstrap_uncertainty.py / permutation_test_n1000.py
│   ├── spatial_logit_glmm.py / morans_i.py / boyce_index.py
│   ├── case_control_sampling.py / cross_site_weight_transfer.py
│   ├── tanager_spectral_ablation.py
│   ├── koflux_nee_validation.py
│   ├── multi_temporal_sancheong.py / hsi_v1_5_smap.py
│   ├── make_grand_hero.py / make_methods_comparison.py
│   ├── make_html_report.py / make_folium_map.py / make_temporal_gif.py
│   └── ... (76 more)
│
├── notebooks/                 ← academic tutorial notebook + reproduction notes
├── wishlist/                  ← 30-scene Tanager Korea wishlist + priority CSV
└── examples/                  ← 16 figures + 27 tables (committed!)
    ├── README.md              ← what each output is
    ├── figures/               ← all hero PNGs + multi-temporal GIF
    ├── maps/                  ← peninsula atlas + 30-scene wishlist
    └── tables/                ← every numerical result as JSON/CSV
```

---

## 6 — System requirements

- **Python 3.11–3.14** (tested on 3.14.3)
- **OS**: Linux / macOS / Windows
- **RAM**: 8 GB minimum for example viewing; 16 GB for full pipeline
- **Disk**: 200 MB for repo only; +156 GB for full pipeline (data layers)
- **GPU**: not required (PyTorch DiffPROSPECT runs CPU in ~5 min)

Key Python deps (full list in `requirements.txt`):
```
numpy, pandas, scikit-learn, scipy, statsmodels
xarray, rioxarray, rasterio, geopandas, shapely
matplotlib, seaborn, folium
prosail, h5netcdf, h5py, earthaccess, pystac-client
streamlit, torch (cpu-only OK), imageio
```

---

## 7 — Pre-registration verification

To verify the weights were committed BEFORE any cross-validation result:

```bash
git log c181cc2 -1 WEIGHTS_FREEZE.md
# Author: Heedo Choi
# Date:   2026-04-29
#
#     v1.0 freeze: SUBMISSION.md ...

git log v1.0..v1.9 --oneline | tail   # all subsequent commits
```

The `WEIGHTS_FREEZE.md` document specifies HSI v1 weights
`(0.40 / 0.20 / 0.30 / 0.10)` and the species pyrophilic priors
*before* the Sancheong / Gangneung / Uljin / Palisades cross-validation
results were ever computed. Git commit hash registration is a pending
administrative step; the substantive evidence is the public Git
commit hash + timestamp.

---

## 8 — Where to find help

- **Reviewer reading guide**: [`REVIEWER_GUIDE.md`](REVIEWER_GUIDE.md)
- **FAQ**: [`REVIEWER_FAQ.md`](REVIEWER_FAQ.md)
- **Issue tracker**: https://github.com/zxsa0716/pinesentry-fire/issues
- **Email**: zxsa0716@kookmin.ac.kr
