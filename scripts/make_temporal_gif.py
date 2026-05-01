"""Animated GIF of Sancheong multi-temporal pre-fire firerisk evolution.

3 frames: T-15mo (2024-12-19) / T-1.5mo (2026-02-10) / T+3d (2026-03-24)
Each frame shows the firerisk_v0 raster derived from the corresponding
EMIT scene + the 2026-03 fire perimeter overlay.

Output: data/hsi/v1/sancheong_temporal.gif
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

OUT = Path("data/hsi/v1/sancheong_temporal.gif")
SCENES = [
    ("T-15mo (2024-12-19)", "data/emit/sancheong/EMIT_L2A_RFL_001_20241219T032003_2435402_004.nc"),
    ("T-1.5mo (2026-02-10)", "data/emit/sancheong/EMIT_L2A_RFL_001_20260210T054113_2604104_011.nc"),
    ("T+3d (2026-03-24)",   "data/emit/sancheong/EMIT_L2A_RFL_001_20260324T054026_2608303_045.nc"),
]
PERI = "data/fire_perimeter/synth_sancheong_dnbr.gpkg"


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


def main():
    import imageio.v3 as iio
    import geopandas as gpd
    peri = gpd.read_file(PERI).to_crs("EPSG:4326")

    frames = []
    for label, path in SCENES:
        p = Path(path)
        if not p.exists():
            print(f"  missing {p}"); continue
        rfl_ds = xr.open_dataset(p, engine="h5netcdf")
        bp = xr.open_dataset(p, engine="h5netcdf", group="sensor_band_parameters")
        loc = xr.open_dataset(p, engine="h5netcdf", group="location")
        wls = bp.wavelengths.values
        rfl = rfl_ds.reflectance.values.astype("float32")
        rfl = np.where(rfl < -1, np.nan, rfl)
        b_red = nearest(wls, 663); b_nir = nearest(wls, 858); b_swir = nearest(wls, 1640)
        ndvi = (rfl[..., b_nir] - rfl[..., b_red]) / (rfl[..., b_nir] + rfl[..., b_red] + 1e-6)
        ndii = (rfl[..., b_nir] - rfl[..., b_swir]) / (rfl[..., b_nir] + rfl[..., b_swir] + 1e-6)
        firerisk = 0.6 * (1 - percentile_norm(ndii)) + 0.4 * (1 - percentile_norm(ndvi))
        glt_x = loc.glt_x.values; glt_y = loc.glt_y.values
        fr_o = orthorectify(firerisk, glt_x, glt_y)
        lat_o = orthorectify(loc.lat.values, glt_x, glt_y)
        lon_o = orthorectify(loc.lon.values, glt_x, glt_y)
        bb = (np.nanmin(lon_o), np.nanmin(lat_o), np.nanmax(lon_o), np.nanmax(lat_o))

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(fr_o, origin="upper", cmap="YlOrRd", vmin=0, vmax=1,
                       extent=[bb[0], bb[2], bb[1], bb[3]])
        peri.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2)
        ax.set_xlim(bb[0], bb[2]); ax.set_ylim(bb[1], bb[3])
        ax.set_title(f"산청 Sancheong — firerisk_v0 — {label}", fontsize=14)
        ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
        plt.colorbar(im, ax=ax, fraction=0.04, label="firerisk_v0 (0=safe, 1=high)")
        fig.tight_layout()
        fig.canvas.draw()
        # Convert to numpy array via PNG buffer (Matplotlib RGBA buffer access)
        from io import BytesIO
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100); plt.close(fig)
        buf.seek(0)
        from PIL import Image
        img = np.array(Image.open(buf).convert("RGB"))
        frames.append(img)
        print(f"  rendered {label}")

    if not frames:
        print("no frames"); return

    # Pad to common shape
    max_h = max(f.shape[0] for f in frames); max_w = max(f.shape[1] for f in frames)
    padded = []
    for f in frames:
        h, w, _ = f.shape
        pad = np.full((max_h, max_w, 3), 255, dtype=np.uint8)
        pad[:h, :w] = f
        padded.append(pad)

    # 1.5s per frame, 3 frames
    OUT.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(OUT, padded, duration=1500, loop=0, plugin="pillow")
    print(f"\nsaved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
