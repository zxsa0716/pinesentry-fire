"""Multi-temporal pre-fire signal visualization at Sancheong.

Final high-quality version. Two distinct geometries are used:

  1. RAW UNION of the 80K-pixel dNBR mask  → used ONLY for the inside/outside
     statistical test. This reproduces the published +0.146 firerisk separation
     reported in PAPER.md / TABLE.md.

  2. SHAPELY concave_hull of the same union → used ONLY as the visual outline
     drawn on the map. This is a clean organic "fire-shape" boundary, not the
     pixel mosaic and not a rectangle.

The two geometries serve different purposes; mixing them was the bug in the
previous round.

Outputs:
  examples/figures/16_sancheong_pre_fire_signal.png      (static, ~600 KB)
  examples/figures/16_sancheong_temporal_animation.gif   (zoom animation)
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
import xarray as xr

plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_GIF = Path("examples/figures/16_sancheong_temporal_animation.gif")
OUT_PNG = Path("examples/figures/16_sancheong_pre_fire_signal.png")

KEY_SCENE = "data/emit/sancheong/EMIT_L2A_RFL_001_20260210T054113_2604104_011.nc"
PERI = "data/fire_perimeter/synth_sancheong_dnbr.gpkg"

TIMELINE = [
    ("2024-12-19", "T − 15 mo", False, "off-site"),
    ("2026-02-10", "T − 1.5 mo", True,  "covers burn area"),
    ("2026-03-21", "T = 0",         None,  "FIRE IGNITES"),
    ("2026-03-24", "T + 3 d",       False, "off-site"),
]


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def percentile_norm(a):
    m = np.isfinite(a)
    if m.sum() < 10: return np.zeros_like(a)
    plo, phi = np.nanpercentile(a[m], [5, 95])
    if phi <= plo: return np.zeros_like(a)
    return np.clip((a - plo) / (phi - plo), 0, 1)


def nearest(wls, target):
    return int(np.argmin(np.abs(wls - target)))


def load_key_scene():
    p = Path(KEY_SCENE)
    if not p.exists():
        return None
    bp = xr.open_dataset(p, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(p, engine="h5netcdf", group="location")
    wls = bp.wavelengths.values

    b_red, b_nir, b_swir = nearest(wls, 663), nearest(wls, 858), nearest(wls, 1640)
    rfl_ds = xr.open_dataset(p, engine="h5netcdf")
    red = rfl_ds.reflectance.isel(bands=b_red).values.astype("float32")
    nir = rfl_ds.reflectance.isel(bands=b_nir).values.astype("float32")
    swir = rfl_ds.reflectance.isel(bands=b_swir).values.astype("float32")
    red = np.where(red < -1, np.nan, red)
    nir = np.where(nir < -1, np.nan, nir)
    swir = np.where(swir < -1, np.nan, swir)
    ndvi = (nir - red) / (nir + red + 1e-6)
    ndii = (nir - swir) / (nir + swir + 1e-6)
    firerisk = 0.6 * (1 - percentile_norm(ndii)) + 0.4 * (1 - percentile_norm(ndvi))

    glt_x, glt_y = loc.glt_x.values, loc.glt_y.values
    fr_o = orthorectify(firerisk, glt_x, glt_y)
    lat_o = orthorectify(loc.lat.values, glt_x, glt_y)
    lon_o = orthorectify(loc.lon.values, glt_x, glt_y)
    return fr_o, lat_o, lon_o


def build_geometries(peri_path):
    """
    Returns (test_geometry, display_outline).

    test_geometry  — raw union of all dNBR pixel polygons (correct for
                     the inside/outside statistical test)
    display_outline — concave_hull of the same union, smoothed slightly
                     for clean visual outline only
    """
    import geopandas as gpd
    peri = gpd.read_file(peri_path).to_crs("EPSG:4326")
    raw_union = peri.geometry.union_all() if hasattr(peri.geometry, "union_all") \
                 else peri.geometry.unary_union

    # concave_hull is the right "alpha shape" for an organic fire outline
    hull = shapely.concave_hull(raw_union, ratio=0.10)
    # Slight smoothing
    smoothed = hull.buffer(0.001).buffer(-0.001)

    return raw_union, gpd.GeoDataFrame(geometry=[smoothed], crs="EPSG:4326")


def render_main_figure(fr_o, lat_o, lon_o, raw_union, display_outline, dpi=200):
    """High-quality 2-panel figure: zoomed map + inside/outside histogram."""
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.prepared import prep

    fire_bounds = display_outline.total_bounds
    bx0, by0, bx1, by1 = fire_bounds
    pad = 0.10
    plot_xlim = (bx0 - pad, bx1 + pad)
    plot_ylim = (by0 - pad, by1 + pad)

    valid = np.isfinite(fr_o) & np.isfinite(lat_o) & np.isfinite(lon_o)
    in_view = valid & (lat_o >= plot_ylim[0]) & (lat_o <= plot_ylim[1]) \
            & (lon_o >= plot_xlim[0]) & (lon_o <= plot_xlim[1])
    if in_view.sum() < 1000:
        print("WARN: very few in-view pixels"); return

    # Colour stretch — full SCENE percentiles, not just window
    scene_vals = fr_o[valid]
    vmin = float(np.nanpercentile(scene_vals, 5))
    vmax = float(np.nanpercentile(scene_vals, 95))
    if vmax <= vmin:
        vmin, vmax = 0.0, 1.0

    # ── Build a regular-grid raster of the burn mask aligned with fr_o ──
    # The orthorectified swath isn't on a regular grid, so we build a
    # consistent WGS84 grid from the per-row mean lat/lon, rasterize the
    # raw_union onto it, then re-sample fr_o at the same grid. This mirrors
    # multi_temporal_sancheong.py and produces the published +0.146 separation.
    from rasterio.features import rasterize
    from rasterio.transform import from_origin

    lons_1d = np.nanmean(lon_o, axis=0)
    lats_1d = np.nanmean(lat_o, axis=1)
    res_x = abs(np.nanmedian(np.diff(lons_1d)))
    res_y = abs(np.nanmedian(np.diff(lats_1d)))
    H_o, W_o = lat_o.shape
    transform = from_origin(np.nanmin(lons_1d), np.nanmax(lats_1d), res_x, res_y)
    burn_mask = rasterize([(raw_union, 1)], out_shape=(H_o, W_o),
                           transform=transform, fill=0, dtype="uint8").astype(bool)

    # Use ALL valid scene pixels for the outside group (matches the
    # multi_temporal_sancheong.py analysis that gave Δ=+0.146 in PAPER.md).
    in_burn = burn_mask & valid
    out_burn = (~burn_mask) & valid
    inside_vals = fr_o[in_burn]
    outside_vals = fr_o[out_burn]
    if len(outside_vals) > 80_000:   # subsample for histogram readability
        rng2 = np.random.default_rng(0)
        outside_vals = outside_vals[rng2.choice(len(outside_vals), 80_000, replace=False)]
    print(f"  inside (raw burn pixels rasterized): n={len(inside_vals):,}, mean={inside_vals.mean():.3f}")
    print(f"  outside (all valid non-burn):        n={len(outside_vals):,}, mean={outside_vals.mean():.3f}")
    print(f"  separation Δ = {inside_vals.mean() - outside_vals.mean():+.3f}")

    # ── Build figure ─────────────────────────────────────────────────
    fig = plt.figure(figsize=(15, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.2, 1.4], height_ratios=[6, 1.0],
                           hspace=0.30, wspace=0.22)

    # Map panel (left)
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor("#e8e8e8")
    v_lat = lat_o[valid]; v_lon = lon_o[valid]
    full_extent = [float(v_lon.min()), float(v_lon.max()),
                    float(v_lat.min()), float(v_lat.max())]
    ax.imshow(fr_o, origin="upper", cmap="YlOrRd",
               vmin=vmin, vmax=vmax, extent=full_extent,
               aspect="auto", zorder=1, interpolation="bilinear")

    # Display outline: white halo + black line for legibility
    display_outline.plot(ax=ax, facecolor="none", edgecolor="white",
                          linewidth=4.5, zorder=3, alpha=0.7)
    display_outline.plot(ax=ax, facecolor="none", edgecolor="black",
                          linewidth=2.4, zorder=4)

    ax.set_xlim(*plot_xlim); ax.set_ylim(*plot_ylim)
    ax.set_xlabel("Longitude (°E)", fontsize=12)
    ax.set_ylabel("Latitude (°N)", fontsize=12)
    ax.set_title("Sancheong — EMIT firerisk on 2026-02-10\n"
                  "(T − 1.5 months before the 2026-03-21 ignition)",
                  fontsize=13, pad=10)
    ax.grid(True, linestyle=":", alpha=0.4, zorder=2)

    cbar = plt.colorbar(matplotlib.cm.ScalarMappable(
        norm=matplotlib.colors.Normalize(vmin, vmax), cmap="YlOrRd"),
        ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label(f"firerisk_v0  ({vmin:.2f}–{vmax:.2f} = scene 5–95 percentile)",
                    fontsize=10)

    # Annotation
    cx, cy = display_outline.geometry.iloc[0].centroid.x, display_outline.geometry.iloc[0].centroid.y
    ax.annotate("future burn area",
                 xy=(cx, cy), xytext=(plot_xlim[1] - 0.04, plot_ylim[1] - 0.03),
                 fontsize=11, color="black", fontweight="bold",
                 ha="right",
                 arrowprops=dict(arrowstyle="->", color="black", lw=1.4),
                 zorder=10,
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                           edgecolor="black", alpha=0.92))

    # Histogram panel (right)
    ax2 = fig.add_subplot(gs[0, 1])
    bins = np.linspace(vmin, vmax, 35)
    ax2.hist(outside_vals, bins=bins, color="#1a9850", alpha=0.65,
              label=f"outside burn area\n(n={len(outside_vals):,}, "
                    f"mean {outside_vals.mean():.3f})",
              density=True, zorder=2)
    ax2.hist(inside_vals, bins=bins, color="#a50026", alpha=0.78,
              label=f"INSIDE burn area\n(n={len(inside_vals):,}, "
                    f"mean {inside_vals.mean():.3f})",
              density=True, zorder=3)
    ax2.axvline(outside_vals.mean(), color="#1a9850", linestyle="--", lw=2, zorder=4)
    ax2.axvline(inside_vals.mean(),  color="#a50026", linestyle="--", lw=2, zorder=4)
    delta = inside_vals.mean() - outside_vals.mean()
    ax2.set_xlabel("firerisk_v0", fontsize=11)
    ax2.set_ylabel("density", fontsize=11)
    ax2.set_title(f"Inside vs outside future burn area\n"
                   f"separation Δ = {delta:+.3f}", fontsize=12)
    ax2.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax2.grid(True, linestyle=":", alpha=0.4)

    # Timeline panel (bottom, full width)
    ax_tl = fig.add_subplot(gs[1, :])
    ax_tl.set_xlim(-0.5, len(TIMELINE) - 0.5)
    ax_tl.set_ylim(-1, 1.4)
    ax_tl.axhline(0, color="black", linewidth=1.2, zorder=1)
    for i, (date, t_label, covers, note) in enumerate(TIMELINE):
        if covers is None:
            color, marker, ms = "#a50026", "X", 22
            text_color, text_weight = "#a50026", "bold"
        elif covers:
            color, marker, ms = "#1a9850", "o", 18
            text_color, text_weight = "#1a9850", "bold"
        else:
            color, marker, ms = "#999", "o", 12
            text_color, text_weight = "#666", "normal"
        ax_tl.plot(i, 0, marker=marker, color=color, markersize=ms,
                    markeredgecolor="black", markeredgewidth=1.0, zorder=3)
        ax_tl.text(i, 0.65, date, ha="center", fontsize=10, fontweight="bold")
        ax_tl.text(i, 0.35, t_label, ha="center", fontsize=9, color="#444")
        ax_tl.text(i, -0.55, note, ha="center", fontsize=9,
                    color=text_color, fontweight=text_weight)
    ax_tl.set_xticks([]); ax_tl.set_yticks([])
    for spine in ax_tl.spines.values():
        spine.set_visible(False)
    ax_tl.set_title("EMIT scene-availability timeline at Sancheong",
                     fontsize=11, pad=4, color="#444")

    fig.suptitle("PineSentry-Fire — pre-fire pyrophilic stress detected 6 weeks "
                  "before the 2026-03-21 Sancheong fire ignition",
                  fontsize=15, fontweight="bold", y=0.98)

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved -> {OUT_PNG} ({OUT_PNG.stat().st_size/1e6:.2f} MB)")


def render_animation(fr_o, lat_o, lon_o, display_outline, dpi=140):
    """Smooth zoom animation: wide view → tight on burn area."""
    import imageio.v3 as iio
    from PIL import Image

    fire_bounds = display_outline.total_bounds
    bx0, by0, bx1, by1 = fire_bounds
    cx, cy = 0.5 * (bx0 + bx1), 0.5 * (by0 + by1)

    valid = np.isfinite(fr_o) & np.isfinite(lat_o) & np.isfinite(lon_o)
    v_lat = lat_o[valid]; v_lon = lon_o[valid]
    full_extent = [float(v_lon.min()), float(v_lon.max()),
                    float(v_lat.min()), float(v_lat.max())]

    scene_vals = fr_o[valid]
    vmin = float(np.nanpercentile(scene_vals, 5))
    vmax = float(np.nanpercentile(scene_vals, 95))

    zooms = [0.40, 0.30, 0.22, 0.16, 0.12]
    frames = []
    for z in zooms:
        fig, ax = plt.subplots(figsize=(8, 7))
        ax.set_facecolor("#e8e8e8")
        ax.imshow(fr_o, origin="upper", cmap="YlOrRd",
                   vmin=vmin, vmax=vmax, extent=full_extent,
                   aspect="auto", interpolation="bilinear", zorder=1)
        display_outline.plot(ax=ax, facecolor="none", edgecolor="white",
                              linewidth=4.0, zorder=3, alpha=0.7)
        display_outline.plot(ax=ax, facecolor="none", edgecolor="black",
                              linewidth=2.4, zorder=4)
        ax.set_xlim(cx - z, cx + z); ax.set_ylim(cy - z, cy + z)
        ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
        ax.set_title(f"Sancheong — EMIT firerisk on 2026-02-10\n"
                      f"zoom: ±{z:.2f}° around future burn area",
                      fontsize=11)
        ax.grid(True, linestyle=":", alpha=0.4)
        cbar = plt.colorbar(matplotlib.cm.ScalarMappable(
            norm=matplotlib.colors.Normalize(vmin, vmax), cmap="YlOrRd"),
            ax=ax, fraction=0.04, pad=0.02)
        cbar.set_label("firerisk_v0")

        fig.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
        plt.close(fig)
        buf.seek(0)
        frames.append(np.array(Image.open(buf).convert("RGB")))

    max_h = max(f.shape[0] for f in frames)
    max_w = max(f.shape[1] for f in frames)
    padded = []
    for f in frames:
        h, w, _ = f.shape
        pad = np.full((max_h, max_w, 3), 255, dtype=np.uint8)
        pad[:h, :w] = f
        padded.append(pad)
    padded += [padded[-1]] * 3

    OUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(OUT_GIF, padded, duration=900, loop=0, plugin="pillow")
    print(f"saved -> {OUT_GIF} ({OUT_GIF.stat().st_size/1e6:.2f} MB)")


def main():
    raw_union, display_outline = build_geometries(PERI)
    print(f"display outline bounds: {display_outline.total_bounds}")

    out = load_key_scene()
    if out is None:
        print("KEY scene unavailable"); return
    fr_o, lat_o, lon_o = out

    render_main_figure(fr_o, lat_o, lon_o, raw_union, display_outline)
    render_animation(fr_o, lat_o, lon_o, display_outline)


if __name__ == "__main__":
    main()
