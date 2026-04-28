"""PineSentry-Fire interactive demo (HuggingFace Spaces deployment target).

Run locally:  streamlit run streamlit_app/app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="PineSentry-Fire",
    page_icon="🌲🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------- Sidebar -----------------------
with st.sidebar:
    st.title("🌲🔥 PineSentry-Fire")
    st.caption("Tanager-trained Hydraulic Stress Index for Korean pine fire prediction")

    site = st.selectbox(
        "Site",
        [
            "의성 (Uiseong 2025) — Primary Hero",
            "산청 (Sancheong 2025) — Dual Hero",
            "광릉 (Gwangneung KoFlux) — sanity",
            "Palisades (LA 2025) — US validation",
            "강원 동해안 atlas",
        ],
        index=0,
    )

    days_pre = st.slider("Days before fire (T-N days)", 0, 90, 14)

    sensor = st.radio("Spectral input", ["Tanager 426 bands (5 nm)", "EMIT 285 bands (7.4 nm)", "Sentinel-2 13 bands"], index=1)

    with st.expander("Advanced — HSI weights"):
        w_safety = st.slider("w_safety (HSM)", 0.0, 1.0, 0.5, 0.05)
        w_water  = st.slider("w_water (EWT)", 0.0, 1.0, 0.3, 0.05)
        w_starch = st.slider("w_starch (LMA)", 0.0, 1.0, 0.2, 0.05)
        st.caption(f"sum = {w_safety + w_water + w_starch:.2f}; default (0.5/0.3/0.2) is OSF-pre-registered")


# ----------------------- Main -----------------------
tab_overview, tab_method, tab_repro, tab_wishlist = st.tabs(
    ["Overview", "Methodology", "Reproducibility", "30-Scene Wishlist"]
)


with tab_overview:
    st.header(f"Pre-fire HSI: {site} (T−{days_pre} days)")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("A. Pre-fire HSI map")
        st.info("Hero figure Panel A — populated by notebook 05/07 outputs (PNG/COG)")
        # TODO: load precomputed HSI raster from HuggingFace Hub or repo
        # st.image("assets/uiseong_hsi_T-14d.png", use_column_width=True)

    with col_b:
        st.subheader("B. + Fire perimeter overlay")
        st.info("Hero figure Panel B — 산림청 GIS perimeter on the same extent")
        # TODO: overlay with folium / pydeck

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("C. Lift chart (Hero core)")
        st.info("HSI decile vs burn fraction with 95% CI")
        # TODO: bar chart from results JSON

    with col_d:
        st.subheader("D. ROC + PR (supplementary)")
        st.info("HSI vs DWI / FWI / KBDI / NDMI / NDVI baselines")
        # TODO: ROC overlay


with tab_method:
    st.header("PineSentry-Fire methodology")
    st.markdown(
        """
**ONE question**: Tanager-derived hydraulic-stress traits jointly explain
(a) 광릉 KoFlux NEE residuals AND (b) 의성·산청 2025 ignition susceptibility,
outperforming weather-only baselines.

**Pipeline**:

1. Tanager L1B → ISOFIT atmospheric correction → BOA reflectance
2. DOFA backbone (frozen) + Wavelength-Prompt + single LoRA rank-16
3. Trait head → 5 channels (LMA, EWT, N, lignin, REIP)
4. DiffPROSAIL/4SAIL2 dual-branch reconstruction loss
5. HSI = w_safety·(1−HSM) + w_water·(1−EWT) + w_starch·LMA
   (physiological prior, Martin-StPaul 2017; OSF pre-registered)
6. EMIT cross-sensor transfer to Korea
7. Spatial logistic GLMM + permutation test on burn perimeter

**Decisive bands** (Tanager-only):
- 1510, 2080 nm (foliar N)
- 970, 1200, 1450 nm (EWT)
- 1690, 2100 nm (lignin)
- 700–740 nm (REIP slope)
        """
    )


with tab_repro:
    st.header("Reproducibility")
    st.markdown(
        """
- **GitHub**: [pinesentry-fire](https://github.com/[user]/pinesentry-fire) (commit-frozen at submission)
- **Zenodo DOI**: pending Week 14
- **Colab**: 1-click reproduction at `colab.ipynb`
- **Docker**: `docker pull [user]/pinesentry-fire:v4.1`
- **OSF pre-registration**: pending submission 2026-05-15
- **Conda env**: `env/environment.yml`

All trained model weights, ISOFIT-corrected reflectance cubes, and intermediate
results are released under CC-BY-4.0 on HuggingFace Hub and Zenodo.
        """
    )


with tab_wishlist:
    st.header("30-Scene Korean Tanager Wishlist")
    st.markdown(
        """
If awarded a top-3 prize, the following 30 Tanager scenes will be released
into the Open STAC catalog (CC-BY) for the global research community:

| Group | Sites | Scenes |
|---|---|---|
| A. 광릉 KoFlux super-site | GDK + CFK | 8 |
| B. 백두대간 conifer ridges | 점봉·지리·덕유·설악 | 6 |
| C. East-coast fire chronosequence | 의성·울진·강릉 | 6 |
| D. 동해안 송이 *P. densiflora* | 봉화·울진 | 4 |
| E. DMZ uncontrolled reference | 강원·경기 DMZ | 3 |
| F. 한라산 elevation gradient | 1100–1950 m | 3 |
| **Total** | | **30** |

**Downstream users**: 산림청 산불대응센터 / 기상청 AsiaFire / IPCC AR7 East Asia regional synthesis.
        """
    )
    # TODO: render korea_30_scenes.geojson on folium map
