"""Render the 30-scene Korean Tanager wishlist on a static map.

Output: wishlist/korea_30_scenes.png — for the README/Streamlit Q7 narrative.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

GEOJSON = Path("wishlist/korea_30_scenes.geojson")
OUT = Path("wishlist/korea_30_scenes.png")


def main():
    if not GEOJSON.exists():
        print(f"missing {GEOJSON}")
        return
    fc = json.loads(GEOJSON.read_text())
    feats = fc["features"]

    region_color = {
        "Gwangneung": "#1a9850",
        "Hwacheon": "#1a9850", "Chuncheon": "#1a9850", "Yangpyeong": "#1a9850", "Gapyeong": "#1a9850",
        "Taebaek": "#fd8d3c", "Sobaek": "#fd8d3c", "Worak": "#fd8d3c", "Songnisan": "#fd8d3c",
        "Deogyu": "#fd8d3c", "Jirisan": "#fd8d3c",
        "Gangneung": "#a50026", "Donghae": "#a50026", "Samcheok": "#a50026",
        "Uljin": "#a50026", "Yeongdeok": "#a50026", "Pohang": "#a50026",
        "Bonghwa": "#984ea3", "Yeongyang": "#984ea3", "Cheongsong": "#984ea3", "Uiseong": "#984ea3",
        "Cheorwon": "#74add1", "Yanggu": "#74add1", "Goseong": "#74add1",
        "Halla": "#fee08b", "Jeju": "#fee08b",
    }

    fig, ax = plt.subplots(figsize=(8, 9))
    for f in feats:
        coords = f["geometry"]["coordinates"][0]
        xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
        region = f["properties"]["region"]
        c = region_color.get(region, "#666666")
        ax.fill(xs, ys, color=c, alpha=0.7, edgecolor="black", linewidth=0.5)
        ax.text(sum(xs)/len(xs), sum(ys)/len(ys), region[:8],
                ha="center", va="center", fontsize=6, color="black")

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("PineSentry-Fire — 30-scene Korean Tanager wishlist (Q7 Next Steps)\n"
                 "Color = region group; if awarded top-3, these go to Open STAC under CC-BY-4.0",
                 fontsize=10)
    ax.set_xlim(125.5, 130.5); ax.set_ylim(33, 39)
    ax.grid(True, linestyle=":", alpha=0.3)

    legend_groups = [
        ("광릉 KoFlux super-site (8)", "#1a9850"),
        ("백두대간 transect (6)", "#fd8d3c"),
        ("동해안 fire-prone (6)", "#a50026"),
        ("송이림 Pinus densiflora (4)", "#984ea3"),
        ("DMZ untouched (3)", "#74add1"),
        ("한라산 + 제주 (3)", "#fee08b"),
    ]
    handles = [mpatches.Patch(color=c, label=l) for l, c in legend_groups]
    ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.95)

    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
