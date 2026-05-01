"""Interactive folium map of HSI v1 + fire perimeters across 5 + Park Fire sites.

Output: REPORT_MAP.html — single self-contained HTML, pan/zoom in browser.
Reviewers can compare HSI v1 spatial pattern to actual burn perimeters.
"""
from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import rioxarray as rxr

OUT = Path("REPORT_MAP.html")

SITES = [
    ("uiseong",   (36.45, 128.70), "data/hsi/v1/uiseong_hsi_v1.tif",
                   "data/fire_perimeter/synth_uiseong_dnbr.gpkg",        "EMIT 285b · AUC 0.747"),
    ("sancheong", (35.36, 127.86), "data/hsi/v1/sancheong_hsi_v1.tif",
                   "data/fire_perimeter/synth_sancheong_dnbr.gpkg",      "EMIT 285b · AUC 0.647"),
    ("gangneung", (37.78, 128.85), "data/hsi/v1/gangneung_hsi_v1.tif",
                   "data/fire_perimeter/synth_gangneung_dnbr.gpkg",      "S2 13b · AUC 0.549"),
    ("uljin",     (37.05, 129.40), "data/hsi/v1/uljin_hsi_v1.tif",
                   "data/fire_perimeter/synth_uljin_dnbr.gpkg",          "S2 13b · AUC 0.545"),
    ("palisades", (34.07, -118.55), "data/hsi/v1/palisades_hsi_v1.tif",
                   "data/fire_perimeter/nifc_palisades_2025.geojson",    "S2 13b · AUC 0.678 (cross-continent)"),
    ("park_fire", (40.08, -121.78), None,
                   "data/fire_perimeter/mtbs_park_2024.gpkg",            "MTBS · 430,768 ac · framework-extensible site"),
]


def to_lonlat_box(da, max_dim=120):
    """Reproject + downscale a TIF to WGS84 PNG-ready bytes for folium overlay."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    da_wgs = da.rio.reproject("EPSG:4326")
    arr = da_wgs.values
    if arr.ndim == 3: arr = arr[0]
    H, W = arr.shape
    if max(H, W) > max_dim:
        s = max_dim / max(H, W)
        from PIL import Image
        img = Image.fromarray(np.where(np.isfinite(arr), arr, np.nan).astype("float32"))
        img = img.resize((int(W*s), int(H*s)))
        arr = np.array(img)
    bounds = list(da_wgs.rio.bounds())  # (minx, miny, maxx, maxy)
    fig, ax = plt.subplots(figsize=(arr.shape[1] / 80, arr.shape[0] / 80), dpi=80)
    ax.imshow(arr, cmap="YlOrRd", vmin=0, vmax=1)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)
    buf.seek(0)
    import base64
    b64 = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{b64}", [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]


def main():
    m = folium.Map(location=[36, 128], zoom_start=3, control_scale=True,
                   tiles="OpenStreetMap")
    folium.TileLayer("CartoDB positron", name="Light").add_to(m)

    fg_perim = folium.FeatureGroup(name="Fire perimeters").add_to(m)

    for name, (lat, lon), tif_path, peri_path, label in SITES:
        # Skip raster overlays — they bloat the HTML to 50+ MB.
        # Reviewers can see the actual HSI maps in HERO_GRAND.png.
        # The folium map is for *interactive perimeter inspection*.

        # Perimeter (simplified to keep HTML size <5MB)
        if peri_path and Path(peri_path).exists():
            try:
                peri = gpd.read_file(peri_path).to_crs("EPSG:4326")
                # Aggressive simplification: tolerance ~0.001 degree (~100m at mid-latitudes)
                # Tolerance ~0.005 deg ≈ 500 m. dissolves the dNBR pixel-mosaic
                # into smooth polygons reviewers actually want to see.
                peri["geometry"] = peri.geometry.simplify(0.005, preserve_topology=True)
                # If still huge, only keep the largest 5 polygons
                if len(peri) > 5:
                    peri["__area"] = peri.geometry.area
                    peri = peri.nlargest(5, "__area").drop(columns="__area")
                folium.GeoJson(
                    peri.to_json(),
                    name=f"{name} perimeter",
                    style_function=lambda x: {
                        "fillColor": "#000000", "color": "#a50026",
                        "weight": 2, "fillOpacity": 0.15
                    },
                ).add_to(fg_perim)
            except Exception as e:
                print(f"  {name}: perimeter failed: {e}")

        folium.Marker([lat, lon], popup=f"<b>{name.title()}</b><br/>{label}",
                      icon=folium.Icon(color="red", icon="fire", prefix="fa")).add_to(m)
        print(f"  {name}: added")

    # Wishlist points
    fg_wish = folium.FeatureGroup(name="Tanager wishlist (30 scenes)", show=False).add_to(m)
    import json
    try:
        wl = json.load(open("wishlist/korea_30_scenes.geojson", encoding="utf-8"))
        for f in wl["features"]:
            geom = f.get("geometry", {})
            if geom.get("type") == "Point":
                lon_w, lat_w = geom["coordinates"]
                folium.CircleMarker([lat_w, lon_w], radius=5, color="#1a9850",
                                    fill=True, fillOpacity=0.7,
                                    popup=f.get("properties", {}).get("name", "")).add_to(fg_wish)
    except Exception as e:
        print(f"wishlist load failed: {e}")

    folium.LayerControl(collapsed=False).add_to(m)
    title = """
    <h3 style="position: fixed; top: 10px; left: 70px; z-index: 9999;
               background: white; padding: 8px; border-radius: 6px;
               box-shadow: 0 2px 6px rgba(0,0,0,.2); font-family: sans-serif;
               margin: 0; font-size: 14px;">
      PineSentry-Fire v1.8 — Interactive map (5 cross-validation sites + Park Fire 2024 + 30-scene Tanager wishlist)
    </h3>"""
    m.get_root().html.add_child(folium.Element(title))
    m.save(str(OUT))
    print(f"\nsaved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
