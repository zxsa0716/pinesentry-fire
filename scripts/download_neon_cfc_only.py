"""Download only NEON CFC (Canopy Foliar Chemistry) + LMA — light, no AOP raster.

CFC: DP1.30012.001 — leaf chemistry table (CSV, ~tens of MB)
LMA: DP1.10026.001 — leaf mass per area table (CSV, ~tens of MB)

Skips the heavy DP3.30006.002 AOP reflectance tiles (10+ GB) which
we'd only need for an end-to-end demo. CFC + LMA alone are enough
to train PROSPECT-D priors per species at Bartlett (BART) and Niwot
(NIWO) which is the Korean conifer/hardwood analogue we need.
"""
from __future__ import annotations

from pathlib import Path

from neonutilities import load_by_product

OUT = Path("data/neon")
SITES = ["BART", "NIWO"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for prod, name in [("DP1.30012.001", "cfc"), ("DP1.10026.001", "lma")]:
        save = OUT / name
        save.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {prod} ({name}) ===")
        load_by_product(
            dpid=prod,
            site=SITES,
            startdate="2023-01",
            enddate="2024-12",
            savepath=str(save),
            check_size=False,
        )
    print(f"\nNEON tables -> {OUT.resolve()}")


if __name__ == "__main__":
    main()
