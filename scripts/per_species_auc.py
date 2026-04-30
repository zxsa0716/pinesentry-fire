"""Per-species AUC breakdown — does HSI v1 work for each Korean conifer cohort?

The pyrophilic factor lumps all pines together at 1.0. This script tests
whether HSI v1 also discriminates burn risk *within* a species by
restricting evaluation to pixels of one Korean Forest Service KOFTR_NM
class at a time.

Output: data/hsi/v1/per_species_auc.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rioxarray as rxr

SITES = ("uiseong", "sancheong")


def main():
    import geopandas as gpd
    from rasterio.features import rasterize
    from sklearn.metrics import roc_auc_score

    summary = {}
    for site in SITES:
        h_path = Path(f"data/hsi/v1/{site}_hsi_v1.tif")
        ims_path = Path(f"data/imsangdo/{site}.gpkg")
        if not ims_path.exists():
            ims_path = None
        peri_path = Path(f"data/fire_perimeter/synth_{site}_dnbr.gpkg")
        if not (h_path.exists() and peri_path.exists() and ims_path):
            print(f"  {site}: missing required input"); continue

        h = rxr.open_rasterio(h_path, masked=True).squeeze()
        peri = gpd.read_file(peri_path).to_crs(h.rio.crs)
        ims = gpd.read_file(ims_path).to_crs(h.rio.crs)

        # Find species column
        col_candidates = [c for c in ims.columns if c.upper() in ("KOFTR_NM", "FRTP_NM", "KOFTR_GROUP_NM")]
        if not col_candidates:
            print(f"  {site}: no species column in imsangdo; cols={list(ims.columns)[:10]}"); continue
        sp_col = col_candidates[0]
        print(f"  {site}: species column = {sp_col}, n_polys={len(ims)}")

        burn_r = rasterize(((g, 1) for g in peri.geometry if g is not None),
                           out_shape=h.shape, transform=h.rio.transform(),
                           fill=0, dtype="uint8").astype(bool)
        valid_h = np.isfinite(h.values)

        per_sp = {}
        for sp_name, sub in ims.groupby(sp_col):
            if not isinstance(sp_name, str) or not sp_name.strip():
                continue
            mask = rasterize(((g, 1) for g in sub.geometry if g is not None),
                             out_shape=h.shape, transform=h.rio.transform(),
                             fill=0, dtype="uint8").astype(bool)
            sub_valid = mask & valid_h
            if sub_valid.sum() < 200:
                continue
            scores = h.values[sub_valid]
            ys = burn_r[sub_valid].astype(int)
            if ys.sum() < 5 or (ys == 0).sum() < 5:
                continue
            try:
                auc = float(roc_auc_score(ys, scores))
            except Exception:
                continue
            per_sp[sp_name] = {
                "n_total": int(sub_valid.sum()),
                "n_burn": int(ys.sum()),
                "auc": auc,
                "mean_score_burned": float(scores[ys == 1].mean()),
                "mean_score_unburned": float(scores[ys == 0].mean()),
            }
        # Sort and report
        ordered = sorted(per_sp.items(), key=lambda kv: -kv[1]["n_total"])
        for k, v in ordered[:10]:
            print(f"     {k}: n={v['n_total']}, burn={v['n_burn']}, AUC={v['auc']:.3f}")
        summary[site] = {sp_col: dict(ordered)}

    Path("data/hsi/v1/per_species_auc.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nsaved -> data/hsi/v1/per_species_auc.json")


if __name__ == "__main__":
    main()
