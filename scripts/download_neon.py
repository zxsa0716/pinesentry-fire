"""Download NEON AOP reflectance + foliar trait labels for sup-training.

No authentication required.

Products:
  DP1.30012.001 — Foliar Chemistry (CFC, leaf nitrogen, lignin, etc.)
  DP1.10026.001 — LMA (Leaf Mass per Area)
  DP3.30006.002 — AOP Spectrometer Reflectance (NIS-1, hyperspectral 426 bands ~5nm)

Sites (matched to PineSentry-Fire's global Tanager training pool):
  BART (Bartlett Forest, NH) — temperate hardwood
  NIWO (Niwot Ridge, CO)     — montane conifer
"""
from __future__ import annotations

from pathlib import Path

try:
    from neonutilities import load_by_product, by_tile_aop
except ImportError:
    print("Install: pip install neonutilities")
    raise

OUT_DIR = Path("data/neon")
SITES = ["BART", "NIWO"]

CFC = "DP1.30012.001"   # Canopy Foliar Chemistry
LMA = "DP1.10026.001"   # LMA
AOP = "DP3.30006.002"   # AOP Reflectance


def download_traits():
    for prod, name in [(CFC, "cfc"), (LMA, "lma")]:
        save = OUT_DIR / name
        save.mkdir(parents=True, exist_ok=True)
        print(f"Loading {prod} ({name}) for {SITES} ...")
        load_by_product(
            dpid=prod,
            site=SITES,
            startdate="2023-01",
            enddate="2024-12",
            savepath=str(save),
            check_size=False,
        )


def download_aop_tiles():
    """Download AOP reflectance tiles co-located with the CFC plots."""
    aop_dir = OUT_DIR / "aop"
    aop_dir.mkdir(parents=True, exist_ok=True)
    # Bartlett tile around plot core
    by_tile_aop(
        dpid=AOP, site="BART", year=2023,
        easting=[316000, 317000], northing=[4881000, 4882000],
        savepath=str(aop_dir),
        check_size=False,
    )
    by_tile_aop(
        dpid=AOP, site="NIWO", year=2023,
        easting=[453000, 454000], northing=[4434000, 4435000],
        savepath=str(aop_dir),
        check_size=False,
    )


if __name__ == "__main__":
    download_traits()
    download_aop_tiles()
    print(f"NEON data → {OUT_DIR.absolute()}")
