"""PineSentry-Fire interactive demo for the August 2026 submission Q8 link.

Local: streamlit run streamlit_app/app.py
Deploy: HuggingFace Spaces (free), pushes from this repo's streamlit_app/
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parents[1]

st.set_page_config(
    page_title="PineSentry-Fire",
    page_icon="🌲🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("🌲🔥 PineSentry-Fire")
    st.caption("EMIT/Tanager-derived Hydraulic Stress Index for Korean pine fire prediction")
    st.markdown(
        "**v1 multi-site result (D-124)**\n\n"
        "| Site | n_burn | AUC | Lift@10% |\n"
        "|---|---:|---:|---:|\n"
        "| Uiseong | 25,804 | **0.747** | 2.30x |\n"
        "| Sancheong | 252 | **0.647** | 1.75x |\n"
    )
    site = st.selectbox(
        "Site",
        ["uiseong", "sancheong"],
        format_func=lambda s: {"uiseong": "의성 Uiseong (2025-03-22)", "sancheong": "산청 Sancheong (2025-03-21)"}[s],
    )

tab_hero, tab_compare, tab_method, tab_wishlist, tab_repro = st.tabs(
    ["Hero figure", "vs Spectral baselines", "Methodology", "30-Scene Wishlist", "Reproducibility"]
)

with tab_hero:
    st.header(f"PineSentry-Fire v1 — {site.title()} pre-fire Hydraulic Stress Index")
    hero = REPO / "data/hsi/v1/HERO_final.png"
    if hero.exists():
        st.image(str(hero), caption="Hero — both sites, identical weights", use_column_width=True)
    eval_png = REPO / f"data/hsi/v1/{site}_eval_v1.png"
    if eval_png.exists():
        st.image(str(eval_png), caption=f"{site.title()} — distribution + ROC + lift", use_column_width=True)

with tab_compare:
    st.header("Spectral baselines (NDVI / NDMI / NDII) vs HSI v1")
    st.markdown(
        "Critical finding — pure spectral indices flip direction across sites:\n"
        "- 의성: high NDVI = burn (raw direction wins)\n"
        "- 산청: high NDMI = NOT burn (inverted direction wins)\n\n"
        "**HSI v1 uses one direction across both sites** — the only model that generalizes."
    )
    for s in ("uiseong", "sancheong"):
        p = REPO / f"data/baselines/{s}_baselines_roc.png"
        if p.exists():
            st.image(str(p), caption=f"{s.title()} — A5 ablation", use_column_width=True)
    summary_path = REPO / "data/baselines/_overall.json"
    if summary_path.exists():
        st.subheader("AUC summary (best baseline direction vs HSI v1)")
        st.json(json.loads(summary_path.read_text()), expanded=False)

with tab_method:
    st.header("Methodology")
    st.markdown(
        """
**One question**: do Tanager/EMIT-derived hydraulic + species-aware traits
predict where Korean pine fires ignite weeks before flames appear?

**Pipeline (v1)**
1. EMIT L2A surface reflectance (winter pre-fire baseline)
2. Spectral proxies — NDII → EWT (mm), NDVI → LMA (g/m²)
3. Imsangdo 1:5,000 KOFTR_NM → species P50 raster (rasterize to ortho grid)
4. Hydraulic safety margin HSM = ψ_min - p50 (Martin-StPaul 2017)
5. Multi-layer fusion:
   ```
   HSI v1 = 0.40·pyrophilic + 0.20·south_facing + 0.30·firerisk_v0 + 0.10·pine_terrain
   ```
   pyrophilic factor: 소나무 1.0, oak 0.5, mesic broadleaf 0.2, non-forest 0.0
6. Sentinel-2 dNBR perimeter as ground-truth label

**Why this works (vs v0)**: empirical NDII/NDVI proxies score winter pines as
hydraulically "safe" — yet pines have low P50 + resin/wax → ignite first.
Adding species pyrophilic + south-facing slope captures the missed signal.
"""
    )

with tab_wishlist:
    st.header("30-Scene Korean Tanager Wishlist (Q7 Next Steps)")
    geo = REPO / "wishlist/korea_30_scenes.geojson"
    if geo.exists():
        try:
            import folium
            from streamlit_folium import st_folium
            data = json.loads(geo.read_text())
            m = folium.Map(location=[36.5, 128.0], zoom_start=7, tiles="cartodbpositron")
            folium.GeoJson(data, name="30 wishlist").add_to(m)
            st_folium(m, height=520)
        except ImportError:
            st.code(geo.read_text()[:5000])
    st.markdown(
        "If awarded a top-3 prize, these 30 Tanager scenes go to Open STAC under CC-BY-4.0:\n"
        "광릉 GDK super-site (8) · 백두대간 transect (6) · 동해안 fire-prone (6) · 송이림 (4) · DMZ (3) · 한라산 (3)."
    )

with tab_repro:
    st.header("Reproducibility")
    st.markdown(
        """
- **GitHub**: https://github.com/zxsa0716/pinesentry-fire (commit-frozen at submission)
- **Zenodo**: DOI to be assigned at OSF freeze
- **Colab**: `colab.ipynb` — 1-click pipeline
- **OSF pre-registration**: weights LOCKED at v1.0 — no post-hoc tuning
- **Env**: `env/environment.yml` (conda) or `pip install -r requirements.txt`
- **License**: CC-BY-4.0 on code + data products

Raw EMIT and Sentinel-2 are obtained via NASA earthaccess + Element84 STAC.
Imsangdo 1:5,000 from data.go.kr (Korean Forest Service).
"""
    )
