# Notebook 07 — Korean East-Coast Pre-Fire HSI Atlas + 30-Scene Wishlist

> Week 11. 운영 prototype + prize 정당화 figure.

## Cells

### Cell 1 — Korean east-coast EMIT scene mosaic (current snapshot)

```python
import earthaccess
emit_korea_recent = earthaccess.search_data(
    short_name="EMITL2ARFL",
    bounding_box=(127.5, 35.5, 130.0, 38.5),  # 동해안 + 백두대간
    temporal=("2025-04-01", "2026-04-26"),
)
```

### Cell 2 — Apply engine → HSI mosaic

```python
from pinesentry_fire.traits import retrieve_traits
from pinesentry_fire.hsi import hydraulic_stress_index

hsi_tiles = []
for scene in emit_korea_recent:
    traits = retrieve_traits(...)
    hsi = hydraulic_stress_index(...)
    hsi_tiles.append(hsi)

mosaic = stack_tiles(hsi_tiles).max(dim="time")  # max stress per pixel
```

### Cell 3 — Filter pine-only pixels (산림청 임상도)

```python
import geopandas as gpd
imsang = gpd.read_file("data/imsangdo/uiseong.gpkg")
pine_mask = imsang.query("FRTP_CD in ['31','32','33']").union_all()  # 침엽수
hsi_pine = mosaic.rio.clip([pine_mask])
```

### Cell 4 — F7 figure: 동해안 pre-fire HSI atlas

```python
fig, ax = plt.subplots(figsize=(12, 16))
hsi_pine.plot(ax=ax, cmap="RdBu_r", vmin=0, vmax=1)
# Overlay: 30-scene wishlist 6 group polygons + labels
# Add: 산림청 산불대응센터 logo + downstream user list
fig.savefig("../figures/F7_korea_atlas.png", dpi=300)
```

### Cell 5 — 30-scene wishlist GeoJSON

```python
import geopandas as gpd
wishlist = gpd.GeoDataFrame({
    "group": ["A"]*8 + ["B"]*6 + ["C"]*6 + ["D"]*4 + ["E"]*3 + ["F"]*3,
    "site":  ["광릉_GDK_봄", "광릉_GDK_여름", ...],
    "geometry": [scene_polygon_1, scene_polygon_2, ...],
})
wishlist.to_file("../wishlist/korea_30_scenes.geojson", driver="GeoJSON")
```

### Cell 6 — Operational hand-off prototype

```python
# 산림청 산불대응센터에 전달 가능한 GeoTIFF 산출
hsi_pine.rio.to_raster("results/korea_eastcoast_pre_fire_hsi.tif")
```

---

## Output

- `figures/F7_korea_atlas.png`
- `wishlist/korea_30_scenes.geojson` (30 polygons)
- `results/korea_eastcoast_pre_fire_hsi.tif` (산림청 hand-off)
