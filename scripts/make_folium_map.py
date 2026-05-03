"""Lightweight interactive folium map of HSI v1 fire perimeters across all sites.

Uses simplified perimeters (convex hull or DP-simplified) so the resulting
HTML stays under 3 MB and ships in the public repo.

Output: REPORT_MAP.html
"""
from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd

OUT = Path("REPORT_MAP.html")

SITES = [
    ("uiseong",   (36.45, 128.70),  "data/fire_perimeter/synth_uiseong_dnbr.gpkg",
        "EMIT 285b · AUC 0.747 · 의성 2025-03"),
    ("sancheong", (35.36, 127.86),  "data/fire_perimeter/synth_sancheong_dnbr.gpkg",
        "EMIT 285b · AUC 0.647 · 산청 2025-03"),
    ("gangneung", (37.78, 128.85),  "data/fire_perimeter/synth_gangneung_dnbr.gpkg",
        "S2 13b · AUC 0.549 · 강릉 2023-04"),
    ("uljin",     (37.05, 129.40),  "data/fire_perimeter/synth_uljin_dnbr.gpkg",
        "S2 13b · AUC 0.545 · 울진 2022-03"),
    ("palisades", (34.07, -118.55), "data/fire_perimeter/nifc_palisades_2025.geojson",
        "S2 13b · AUC 0.678 · LA Palisades 2025-01 (cross-continent)"),
    ("park_fire", (40.08, -121.78), "data/fire_perimeter/mtbs_park_2024.gpkg",
        "MTBS · 430,768 ac · Park Fire 2024 (framework-extensible site)"),
]

COLOR = {
    "uiseong": "#a50026", "sancheong": "#d73027",
    "gangneung": "#fc8d59", "uljin": "#fd8d3c",
    "palisades": "#fdae61", "park_fire": "#984ea3",
}


def main():
    m = folium.Map(location=[36, 128], zoom_start=3, control_scale=True,
                   tiles="OpenStreetMap")
    folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    folium.TileLayer("OpenStreetMap", name="Street").add_to(m)

    fg_perim = folium.FeatureGroup(name="Fire perimeters (simplified)").add_to(m)

    for name, (lat, lon), peri_path, label in SITES:
        if peri_path and Path(peri_path).exists():
            try:
                peri = gpd.read_file(peri_path).to_crs("EPSG:4326")
                # Convert to convex hull (very few vertices) — keeps HTML small
                # while preserving the spatial extent of the burn area.
                peri_hull = peri.geometry.union_all().convex_hull \
                    if hasattr(peri.geometry, "union_all") else peri.geometry.unary_union.convex_hull
                gj = gpd.GeoDataFrame({"name": [name]}, geometry=[peri_hull], crs="EPSG:4326")
                folium.GeoJson(
                    gj.to_json(),
                    name=f"{name} hull",
                    style_function=lambda x, c=COLOR.get(name, "#a50026"): {
                        "fillColor": c, "color": c,
                        "weight": 2, "fillOpacity": 0.20,
                    },
                    tooltip=label,
                ).add_to(fg_perim)
            except Exception as e:
                print(f"  {name}: perimeter failed: {e}")

        folium.Marker(
            [lat, lon],
            popup=f"<b>{name.title()}</b><br/>{label}",
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(m)
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
                folium.CircleMarker(
                    [lat_w, lon_w], radius=5, color="#1a9850",
                    fill=True, fillOpacity=0.7,
                    popup=f.get("properties", {}).get("name", ""),
                ).add_to(fg_wish)
    except Exception as e:
        print(f"wishlist load failed: {e}")

    folium.LayerControl(collapsed=False).add_to(m)

    title = """
    <h3 style="position: fixed; top: 10px; left: 70px; z-index: 9999;
               background: white; padding: 8px; border-radius: 6px;
               box-shadow: 0 2px 6px rgba(0,0,0,.2); font-family: sans-serif;
               margin: 0; font-size: 14px;">
      PineSentry-Fire — Interactive map (5 cross-validation sites + Park Fire 2024 + 30-scene Tanager wishlist)
    </h3>"""
    m.get_root().html.add_child(folium.Element(title))
    m.save(str(OUT))
    print(f"\nsaved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
