"""PineSentry-Fire interactive demo for the August 2026 submission Q8 link.

Local: streamlit run streamlit_app/app.py
Deploy: HuggingFace Spaces (free) — see HUGGINGFACE_SPACES.md

This app is the primary interactive deliverable for the **Code & Scripts**
competition track. It loads pre-committed example outputs from
`examples/figures/` and `examples/tables/` so it works on any fresh clone
without re-running the pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parents[1]
EX_FIG = REPO / "examples" / "figures"
EX_TAB = REPO / "examples" / "tables"
EX_MAP = REPO / "examples" / "maps"


def safe_image(path: Path, **kw):
    if path.exists():
        st.image(str(path), **kw)
    else:
        st.caption(f"_(missing: {path.relative_to(REPO)})_")


def safe_json(path: Path):
    if not path.exists():
        st.caption(f"_(missing: {path.relative_to(REPO)})_")
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except UnicodeDecodeError:
        return json.load(open(path, encoding="cp949"))


st.set_page_config(
    page_title="PineSentry-Fire",
    page_icon="🌲🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌲🔥 PineSentry-Fire")
    st.caption("Tanager 2026 submission")
    st.markdown(
        "Pre-fire **Hydraulic Stress Index** for Korean *Pinus densiflora* + "
        "cross-continent generalization to LA chaparral."
    )
    st.markdown("---")
    st.markdown(
        "**Headline result (5 sites · identical pre-registered weights)**\n\n"
        "| Site | Sensor | AUC |\n"
        "|---|---|---:|\n"
        "| 의성 Uiseong | EMIT 285b | **0.747** |\n"
        "| 산청 Sancheong | EMIT 285b | 0.647 |\n"
        "| 강릉 Gangneung | S2 13b | 0.549 |\n"
        "| 울진 Uljin | S2 13b | 0.545 |\n"
        "| **US Palisades** | S2 13b | **0.678** |\n"
    )
    st.markdown("---")
    st.markdown(
        "**Pre-registration**: weights locked at git commit `c181cc2` "
        "(2026-04-29) — *before* any cross-validation result was committed.\n\n"
        "**License**: CC-BY-4.0\n\n"
        "**GitHub**: [zxsa0716/pinesentry-fire](https://github.com/zxsa0716/pinesentry-fire)"
    )

# ────────────────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────────────────
st.title("PineSentry-Fire — Tanager Open Data Competition 2026")
st.markdown(
    "**EMIT-aligned, species-aware, pre-registered Hydraulic Stress Index** "
    "for predicting where the next pine fire will ignite, *before* it ignites."
)

# ────────────────────────────────────────────────────────────────────────
# Tabs
# ────────────────────────────────────────────────────────────────────────
tab_overview, tab_hero, tab_5site, tab_method, tab_stats, tab_inv, tab_dual, \
    tab_temporal, tab_wishlist, tab_repro = st.tabs([
    "📋 Overview",
    "🎨 Hero figures",
    "📊 5-site results",
    "🧪 Methodology",
    "🔬 Statistical battery",
    "🧬 Trait inversion",
    "🌳 Dual-validation",
    "⏱ Pre-fire temporal",
    "🗺 Q7 wishlist",
    "🔁 Reproducibility",
])

# ── Overview
with tab_overview:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
### Question
Can imaging-spectrometer reflectance + Korean Forest Service stand-level
species data + topography predict **where the next pine fire will ignite**,
*before* it ignites?

### Method (one paragraph)
Per-pixel Hydraulic Stress Index as a fixed convex combination of
**(i)** species pyrophilic factor from Korean Forest Service 1:5,000
임상도 (3.41 M polygons), **(ii)** south-facing slope from COP-DEM 30 m,
**(iii)** EMIT 285-band SWIR firerisk_v0 (NDII / NDVI / red-edge senescence),
and **(iv)** species × terrain interaction.
Weights `(0.40 / 0.20 / 0.30 / 0.10)` are **pre-registered at public git
commit `c181cc2`** (2026-04-29), *before* the v1 cross-validation runs.
Cross-validate on 5 fires (4 Korean + 1 US chaparral) with **identical
weights** and a 9-test statistical battery.

### Why it can win — 5 differentiators
1. **Git-timestamp-locked pre-registration** on weights — no other
   submission can demonstrate "we did not tune to test data" with a
   public commit hash. Verify via `git log c181cc2 -1`.
2. **Korean Forest Service 임상도 1:5,000** (3.41 M polygons).
   Removing this layer drops Uiseong AUC by 0.108 — largest single
   component contribution.
3. **Cross-continent generalization** — Korean conifer-tuned weights
   work on US chaparral (Palisades AUC 0.678).
4. **Honest negative results documented** — RT inversion underperforms,
   DL spatially overfits, NEE opposite-sign at deciduous GDK.
5. **Tanager 30-scene Korean wishlist** with HSI v1 prioritization
   directly answers Q7.
""")
    with col2:
        st.markdown("**Headline figure**")
        safe_image(EX_FIG / "01_HERO_GRAND_9panel.png", use_column_width=True)

# ── Hero
with tab_hero:
    st.header("Hero figures")
    st.markdown("**9-panel Grand Hero**")
    safe_image(EX_FIG / "01_HERO_GRAND_9panel.png", use_column_width=True)
    st.markdown("---")
    st.markdown("**6-panel methods comparison**")
    safe_image(EX_FIG / "02_HERO_methods_6panel.png", use_column_width=True)
    st.markdown("---")
    st.markdown("**5-site bootstrap ROC envelope (95 % bands)**")
    safe_image(EX_FIG / "03_HERO_roc_envelope_5site.png", use_column_width=True)
    st.markdown("---")
    st.markdown("**Original v1.0 dual-site Hero**")
    safe_image(EX_FIG / "04_HERO_final_dual.png", use_column_width=True)

# ── 5-site
with tab_5site:
    st.header("5-site cross-validation (identical pre-registered weights)")
    boot = safe_json(EX_TAB / "bootstrap_5site_95CI.json") or {}
    rows = []
    for s, d in boot.items():
        rows.append({
            "Site": s.title(),
            "n burn": int(d.get("n_burned_total", 0)),
            "n unburn": int(d.get("n_unburned_total", 0)),
            "AUC": round(d.get("auc_mean", 0), 4),
            "95% CI lo": round(d.get("auc_q025", 0), 4),
            "95% CI hi": round(d.get("auc_q975", 0), 4),
            "Lift@10%": round(d.get("lift_mean", 0), 2),
        })
    st.dataframe(rows, use_container_width=True)

    st.markdown("---")
    st.markdown("**Bootstrap CIs visualized**")
    safe_image(EX_FIG / "05_bootstrap_95CI.png", use_column_width=True)

    st.markdown("---")
    col_u, col_s, col_p = st.columns(3)
    with col_u:
        st.markdown("**Uiseong eval (EMIT)**")
        safe_image(EX_FIG / "13_uiseong_eval.png", use_column_width=True)
    with col_s:
        st.markdown("**Sancheong eval (EMIT)**")
        safe_image(EX_FIG / "14_sancheong_eval.png", use_column_width=True)
    with col_p:
        st.markdown("**Palisades eval (S2)**")
        safe_image(EX_FIG / "15_palisades_eval.png", use_column_width=True)

# ── Methodology
with tab_method:
    st.header("Methodology")
    st.markdown("""
```
HSI v1(i) = 0.40 · pyrophilic(i)
          + 0.20 · south_facing(i)
          + 0.30 · firerisk_v0(i)
          + 0.10 · (pyrophilic × south_facing)(i)
```

Each component is rescaled to [0, 1] via the 5–95 percentile range
within each scene to make the index sensor-agnostic.

| Component | Source | Rationale |
|---|---|---|
| `pyrophilic` | Korean Forest Service 1:5,000 임상도 (FRTP_NM) | 소나무=1.0, 잣나무=0.85, oak=0.5, mesic broadleaf=0.2, non-forest=0 |
| `south_facing` | COP-DEM 30 m aspect | cos(aspect − 180°), thresholded |
| `firerisk_v0` | EMIT 285b NDII + NDVI + red-edge senescence | Empirical proxy beating PROSPECT-D inversion at this task |
| `pine_terrain` | (pyrophilic × south_facing) | Captures species-on-aspect effect |
""")
    st.markdown("---")
    st.markdown("**Per-band AUC scan across 285 EMIT bands**")
    safe_image(EX_FIG / "09_decisive_bands_285b.png", use_column_width=True)

# ── Statistical battery
with tab_stats:
    st.header("9-test statistical battery (all 5 sites)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Permutation null (N = 1000) — all 5 sites p < 1/1000**")
        safe_image(EX_FIG / "06_permutation_null_N1000.png", use_column_width=True)
    with col_b:
        st.markdown("**Boyce continuous index — EMIT sites textbook monotonic**")
        safe_image(EX_FIG / "07_boyce_index.png", use_column_width=True)

    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**A1–A4 leave-one-out ablation**")
        safe_image(EX_FIG / "08_A1_A4_ablations.png", use_column_width=True)
    with col_d:
        st.markdown("**A6 weight ±20% sensitivity**")
        safe_image(EX_FIG / "12_sensitivity_pm20pct.png", use_column_width=True)

    st.markdown("---")
    st.markdown("**GEE spatial-logit (R-INLA equivalent)**")
    glmm = safe_json(EX_TAB / "GEE_spatial_logit.json") or {}
    rows_g = [
        {"Site": s.title(),
         "n": d.get("n", 0),
         "n clusters": d.get("n_clusters", 0),
         "OR(HSI)": round(d.get("odds_ratio", 0), 2),
         "Wald z": round(d.get("wald_z", 0), 2),
         "p": d.get("p", "—") if isinstance(d.get("p"), str) else f"{d.get('p', 1):.2e}",
         "Significant": "✅" if d.get("p", 1) < 0.05 else "❌"}
        for s, d in glmm.items()
    ]
    st.dataframe(rows_g, use_container_width=True)

    st.markdown("---")
    st.markdown("**Calibration: Brier scores raw vs isotonic**")
    safe_image(EX_FIG / "10_calibration_isotonic.png", use_column_width=True)

    st.markdown("---")
    st.markdown("**Precision-recall**")
    safe_image(EX_FIG / "11_PR_curves.png", use_column_width=True)

# ── Trait inversion
with tab_inv:
    st.header("Trait inversion variants — honest negative results")
    rows_inv = [
        {"Variant": "v0 empirical NDII/NDVI", "Method": "fixed proxy", "AUC (Uiseong)": 0.697},
        {"Variant": "v1 full HSI", "Method": "empirical + species + terrain", "AUC (Uiseong)": 0.747},
        {"Variant": "v2 PROSPECT-D leaf MLP", "Method": "physics, leaf", "AUC (Uiseong)": 0.648},
        {"Variant": "v2.5 PROSAIL canopy MLP", "Method": "physics, canopy + soil", "AUC (Uiseong)": 0.608},
        {"Variant": "v2.7 scipy DiffPROSAIL (finite-diff)", "Method": "L-BFGS-B", "AUC (Uiseong)": 0.500},
        {"Variant": "v2.8 PyTorch DiffPROSAIL (autograd)", "Method": "Adam, 80 steps", "AUC (Uiseong)": 0.683},
    ]
    st.dataframe(rows_inv, use_container_width=True)
    st.markdown("""
**Honest finding**: pure leaf / canopy radiative-transfer inversion under-
performs the empirical NDII proxy on conifer fire risk. Volatile resin /
wax / lignin / crown architecture are not parameterized by PROSAIL but
appear implicit in NDII. PyTorch autograd (v2.8) recovers a real signal
that the scipy finite-diff variant (v2.7) misses — but still under-
performs HSI v1 by 0.064 AUC.
""")

# ── Dual-validation
with tab_dual:
    st.header("Dual-validation — KoFlux GDK NEE residual (legacy 2006-2008)")
    nee = safe_json(EX_TAB / "koflux_NEE_dual_validation.json") or {}
    if "pooled_2006_2008" in nee:
        p = nee["pooled_2006_2008"]
        col_n, col_r, col_p = st.columns(3)
        with col_n:
            st.metric("Pooled n (2006-2008)", f"{p.get('n', 0):,}")
        with col_r:
            st.metric("Pearson r (NEE vs stress)", f"{p.get('pearson_r', 0):+.3f}")
        with col_p:
            st.metric("p-value", f"{p.get('pearson_p', 1):.2e}")

    st.markdown("""
v4.1 design called for testing whether hydraulic-stress traits jointly
explain (a) GDK NEE residuals + (b) ignition susceptibility. We use
**legacy 2006-2008 KoFlux GDK CSVs** (Tanager-era unavailable —
substituted).

Sign is **opposite** the conifer fire hypothesis — GDK is deciduous oak,
summer photosynthesis is light-limited. This confirms the hydraulic NEE
signal is real *and* clarifies that Korean conifer ecosystems are
**physiologically distinct** from the GDK deciduous benchmark.
""")

# ── Multi-temporal
with tab_temporal:
    st.header("Multi-temporal pre-fire signal (Sancheong 2026)")
    st.markdown("""
**EMIT detects pre-fire pyrophilic stress 6 weeks before ignition.**
At 2026-02-10 (T−1.5 mo), mean firerisk_v0 = 0.857 inside the burn polygon
vs 0.711 outside (Δ = +0.146, MW p ≈ 0, n_burn = 13,323 pixels).
""")
    gif_path = EX_FIG / "16_sancheong_temporal_T-1.5mo_animation.gif"
    if gif_path.exists():
        st.image(str(gif_path), caption="Sancheong firerisk_v0 — T−15mo / T−1.5mo / T+3d", use_column_width=True)

# ── Wishlist
with tab_wishlist:
    st.header("Q7 — 30-scene Korean Tanager wishlist (HSI v1 prioritized)")
    safe_image(EX_MAP / "korea_30_scene_wishlist.png", use_column_width=True)
    st.markdown("---")
    st.markdown("**Top 7 ranked by predicted HSI v1**")
    pri = safe_json(EX_TAB / "wishlist_30_scenes_priority.json") or []
    rows_w = [
        {"#": i + 1,
         "name": r.get("name", "")[:50],
         "region": r.get("region", ""),
         "pred HSI v1": r.get("predicted_HSI_v1"),
         "atlas ROI": r.get("atlas_roi", "")}
        for i, r in enumerate(pri[:7])
    ]
    st.dataframe(rows_w, use_container_width=True)

# ── Reproducibility
with tab_repro:
    st.header("Reproducibility")
    st.markdown("""
- **GitHub**: https://github.com/zxsa0716/pinesentry-fire (commit-frozen at submission)
- **Pre-registration**: `WEIGHTS_FREEZE.md` git-locked at commit `c181cc2`
- **Colab**: open `colab.ipynb` — 1-click pipeline + view all examples
- **Local install**: `pip install -r requirements.txt`; `PYTHONPATH=src pytest tests/` → 9/9
- **License**: CC-BY-4.0 on code + data products
- **HuggingFace Spaces deployment**: see `HUGGINGFACE_SPACES.md` for steps

Raw EMIT and Sentinel-2 are obtained via NASA earthaccess + Element84 STAC.
임상도 1:5,000 from data.go.kr (Korean Forest Service product 3045619).
""")
    st.markdown("---")
    st.markdown("**Reading guide for reviewers** — see `REVIEWER_GUIDE.md` for 5/15/full reading paths.")
