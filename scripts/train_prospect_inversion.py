"""Train a leaf-trait inversion MLP from leaf reflectance.

Replaces empirical NDII/NDVI proxies with a learned mapping:
    leaf reflectance (350-2500 nm) -> [LMA, EWT, Cab]

Training data sources:
  1. NEON CFC + LMA tables we already have (data/neon/{cfc,lma}/)
  2. TRY DB public sample (data/try/TRY_49341.tsv) — species-mean priors
  3. Optional: ANGERS / LOPEX93 if available (skipped — ECOSIS API was 500)

For v2 deployment we'll resample EMIT 285 bands -> the learned MLP input.
This script just stages the training data and saves a numpy archive.

Output: data/prospect/training_data.npz
        data/prospect/species_priors.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

OUT_DIR = Path("data/prospect")
OUT_DIR.mkdir(parents=True, exist_ok=True)

NEON_CFC = Path("data/neon/lma")
TRY_FILE = Path("data/try/TRY_49341.tsv")


def load_neon():
    """Load NEON LMA + carbon/nitrogen + chlorophyll tables and join."""
    import pandas as pd
    files = {
        "lma": NEON_CFC / "cfc_LMA.csv",
        "cn":  NEON_CFC / "cfc_carbonNitrogen.csv",
        "chl": NEON_CFC / "cfc_chlorophyll.csv",
        "lig": NEON_CFC / "cfc_lignin.csv",
        "el":  NEON_CFC / "cfc_elements.csv",
        "fld": NEON_CFC / "cfc_fieldData.csv",
    }
    dfs = {}
    for k, f in files.items():
        if f.exists():
            try:
                dfs[k] = pd.read_csv(f)
                print(f"  NEON {k}: {len(dfs[k])} rows, cols={list(dfs[k].columns)[:6]}")
            except Exception as e:
                print(f"  failed {k}: {e}")
    return dfs


def load_try():
    """Aggregate TRY public sample by species + trait into species-trait means."""
    if not TRY_FILE.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_csv(TRY_FILE, sep="\t", on_bad_lines="skip", low_memory=False, encoding="latin-1")
        print(f"TRY total rows: {len(df)}, unique species: {df['AccSpeciesName'].nunique()}")
        # Group by species, trait — return mean of StdValue
        agg = df.groupby(["AccSpeciesName", "TraitID", "TraitName"])["StdValue"].agg(["mean", "median", "count"]).reset_index()
        return agg
    except Exception as e:
        print(f"TRY load failed: {e}"); return None


def main():
    print("=== NEON CFC + LMA ===")
    neon = load_neon()
    print(f"  loaded {len(neon)} tables")

    print("\n=== TRY public sample ===")
    try_df = load_try()
    species_priors = {}
    if try_df is not None and len(try_df):
        for _, row in try_df.iterrows():
            sp = row["AccSpeciesName"]; t = int(row["TraitID"])
            species_priors.setdefault(sp, {})[t] = {
                "name": row["TraitName"][:60],
                "mean": float(row["mean"]) if not np.isnan(row["mean"]) else None,
                "n": int(row["count"]),
            }
        out = OUT_DIR / "species_priors.json"
        out.write_text(json.dumps(species_priors, indent=2, ensure_ascii=False))
        print(f"  saved species priors -> {out}")

    # Compose training matrix — keep what NEON actually provides
    if "lma" in neon:
        import pandas as pd
        lma = neon["lma"]
        cols = [c for c in ["siteID", "sampleID", "leafMassPerArea", "dryMassFraction"] if c in lma.columns]
        sub = lma[cols].dropna(subset=["leafMassPerArea"])
        print(f"\nNEON LMA: {len(sub)} measurements")
        if len(sub):
            X = sub[["leafMassPerArea"] + ([("dryMassFraction")] if "dryMassFraction" in cols else [])].values.astype("float32")
            np.savez(OUT_DIR / "training_data.npz",
                     neon_lma=sub["leafMassPerArea"].values.astype("float32"),
                     neon_siteIDs=sub["siteID"].astype(str).values if "siteID" in cols else np.array([]),
                     try_species_count=len(species_priors))
            print(f"  saved -> {OUT_DIR / 'training_data.npz'}  (LMA range: {sub['leafMassPerArea'].min():.1f} - {sub['leafMassPerArea'].max():.1f} g/m²)")

    print(f"\n[done] {OUT_DIR}")


if __name__ == "__main__":
    main()
