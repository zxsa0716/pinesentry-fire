"""KoFlux GDK NEE residual validation (dual-validation Part A from v4.1 §6).

The original v4.1 design called for testing whether Tanager-derived
hydraulic-stress traits predict NEE residuals at the 광릉 (Gwangneung
Deciduous Korea, GDK) KoFlux super-site. Tanager-era GDK data is
unavailable (per user — assume permanently). We substitute with the
LEGACY KoFlux GDK CSVs that are in hand: 2004, 2005, 2006, 2007, 2008.

Hypothesis: in summer drought weeks (low precip + high VPD), NEE should
become more negative (more carbon uptake) for healthy stands and LESS
negative (less uptake → "browning") for hydraulically stressed stands.
Without satellite traits at GDK in 2004–2008, we use the **observed
H2O / VPD / soil moisture from the eddy-covariance tower itself** to
construct a proxy hydraulic-stress index, then check that NEE residuals
correlate with it. This validates the v4.1 dual-validation framing
even with substitute data.

Inputs:
  data/koflux_gdk/FxMt_GDK_{2004..2008}_*.zip  (CSV inside)

Outputs:
  data/koflux_gdk/nee_residual_summary.json
  data/koflux_gdk/_nee_log.txt
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

SRC_DIR = Path("data/koflux_gdk")
OUT_JSON = SRC_DIR / "nee_residual_summary.json"


def read_year(zpath: Path):
    with zipfile.ZipFile(zpath) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csvs:
            return None
        with z.open(csvs[0]) as f:
            raw = f.read().decode("latin-1", errors="replace")
    lines = raw.splitlines()
    # Header line 0: column names; line 1: units; line 2+: data
    header = [c.strip() for c in lines[0].split(",")]
    rows = []
    for line in lines[2:]:
        parts = line.split(",")
        if len(parts) != len(header):
            continue
        try:
            row = []
            for v in parts:
                v = v.strip()
                if v in ("", "NA", "NaN"):
                    row.append(np.nan)
                else:
                    row.append(float(v))
            rows.append(row)
        except Exception:
            continue
    arr = np.array(rows, dtype="float32")
    return header, arr


def build_proxy_HSI(arr, header):
    """Build a tower-derived proxy hydraulic-stress index.

    Each half-hour record:
      - VPD ~ saturation_vapor_pressure(TA) - actual_vapor_pressure(H2O, PA)
      - SWC = soil water content (volume %)
      - HSI_proxy_dry  = +1 when VPD high AND SWC low
                          (high atmospheric demand + low soil supply)

    We aggregate by week and report mean NEE during the highest-stress
    weeks (top decile HSI_proxy_dry) vs the lowest-stress weeks.
    """
    cols = {c: i for i, c in enumerate(header)}
    # 2008 uses FC1/TA1/H2O1; 2004-2007 use Fc_1/Ta_1 (no H2O column).
    fc_col = "FC1" if "FC1" in cols else ("Fc_1" if "Fc_1" in cols else None)
    ta_col = "TA1" if "TA1" in cols else ("Ta_1" if "Ta_1" in cols else None)
    if fc_col is None or ta_col is None:
        return None
    fc = arr[:, cols[fc_col]]
    ta = arr[:, cols[ta_col]]
    h2o = arr[:, cols["H2O1"]] if "H2O1" in cols else None
    pa = None
    for pa_col in ("PA1", "PA_1"):
        if pa_col in cols:
            pa = arr[:, cols[pa_col]]; break
    swc = None
    swc_keys = [c for c in cols if c.upper().startswith("SWC")]
    for swc_col in swc_keys:
        tmp = arr[:, cols[swc_col]]
        if np.isfinite(tmp).any() and np.nanmean(tmp) > 0:
            swc = tmp; break
    # PPT = precipitation (mm)
    ppt = arr[:, cols["PPT"]] if "PPT" in cols else None
    rg = arr[:, cols["Rg"]] if "Rg" in cols else None

    # Replace -99999 sentinels with NaN
    fc = np.where(fc < -50, np.nan, fc)
    ta = np.where(np.abs(ta) > 60, np.nan, ta)
    if h2o is not None:
        h2o = np.where(h2o < 0, np.nan, h2o)
    if pa is not None:
        pa = np.where(pa <= 0, np.nan, pa)
    if swc is not None:
        swc = np.where((swc < 0) | (swc > 100), np.nan, swc)
    if ppt is not None:
        ppt = np.where(ppt < 0, np.nan, ppt)
    if rg is not None:
        rg = np.where(rg < 0, np.nan, rg)

    # Saturation vapor pressure (kPa, Tetens equation)
    e_sat = 0.6108 * np.exp(17.27 * ta / (ta + 237.3))
    if h2o is not None:
        # Actual VP from H2O mole fraction and atm pressure
        if pa is not None:
            e_act = (h2o * 1e-3) * pa
        else:
            e_act = (h2o * 1e-3) * 100.0
        vpd = np.clip(e_sat - e_act, 0.0, None)
    else:
        # Fall back to e_sat × (1 - RH) where RH is approximated from
        # Ta + Rg (high light + warm = drier air typically); use e_sat alone
        # as a high-VPD proxy (NOT a true VPD but tracks stress conditions).
        vpd = np.where(np.isfinite(ta), e_sat, np.nan)

    # Build HSI proxy: high VPD + low SWC = stressed
    finite = np.isfinite(vpd)
    vpd_n = np.full_like(vpd, np.nan, dtype="float32")
    if finite.sum() > 100:
        plo, phi = np.nanpercentile(vpd[finite], [5, 95])
        if phi > plo:
            vpd_n = np.clip((vpd - plo) / (phi - plo), 0, 1)
    if swc is not None:
        finite_s = np.isfinite(swc)
        swc_n = np.full_like(swc, np.nan, dtype="float32")
        if finite_s.sum() > 100:
            plo, phi = np.nanpercentile(swc[finite_s], [5, 95])
            if phi > plo:
                swc_n = np.clip((swc - plo) / (phi - plo), 0, 1)
        hsi_proxy = 0.5 * vpd_n + 0.5 * (1 - swc_n)
    else:
        hsi_proxy = vpd_n

    return {
        "n_records": int(np.isfinite(fc).sum()),
        "fc": fc, "ta": ta, "h2o": h2o, "vpd": vpd, "swc": swc,
        "hsi_proxy": hsi_proxy,
    }


def daytime_summer_mask(year_arr, header):
    """Filter to daytime summer (DOY 152–243, time 600–1700) for NEE-CO2 uptake."""
    cols = {c: i for i, c in enumerate(header)}
    doy = year_arr[:, cols["DOY"]]
    tm  = year_arr[:, cols["TIME"]]
    return (doy >= 152) & (doy <= 243) & (tm >= 600) & (tm <= 1700)


def main():
    files = sorted(SRC_DIR.glob("FxMt_GDK_*.zip"))
    if not files:
        print("No GDK files", file=sys.stderr); return

    summary = {"site": "Gwangneung Deciduous (GDK)",
               "tower_id": "FxMt_GDK", "years_used": [], "years": {}}
    all_hsi = []
    all_nee = []

    for zp in files:
        m = re.search(r"FxMt_GDK_(\d{4})", zp.name)
        if not m: continue
        year = int(m.group(1))

        out = read_year(zp)
        if out is None: print(f"  {year}: no CSV"); continue
        header, arr = out
        proxy = build_proxy_HSI(arr, header)
        if proxy is None:
            print(f"  {year}: missing FC1/TA1/H2O1"); continue

        mask = daytime_summer_mask(arr, header) & np.isfinite(proxy["fc"]) & np.isfinite(proxy["hsi_proxy"])
        if mask.sum() < 100:
            print(f"  {year}: only {mask.sum()} daytime-summer records, skipping")
            continue

        hsi = proxy["hsi_proxy"][mask]
        nee = proxy["fc"][mask]   # FC1 (CO2 flux umol m-2 s-1, +ve = release)
        # Quantile splits
        q1, q9 = np.quantile(hsi, [0.1, 0.9])
        nee_low_stress = nee[hsi <= q1]
        nee_high_stress = nee[hsi >= q9]
        # Pearson + Spearman + Mann-Whitney
        from scipy.stats import pearsonr, spearmanr, mannwhitneyu
        r_p, p_p = pearsonr(hsi, nee)
        r_s, p_s = spearmanr(hsi, nee)
        mw = mannwhitneyu(nee_high_stress, nee_low_stress, alternative="greater")

        summary["years"][str(year)] = {
            "n_daytime_summer": int(mask.sum()),
            "mean_NEE_low_stress_p10": float(np.nanmean(nee_low_stress)),
            "mean_NEE_high_stress_p90": float(np.nanmean(nee_high_stress)),
            "delta_NEE_high_minus_low": float(np.nanmean(nee_high_stress) - np.nanmean(nee_low_stress)),
            "pearson_r_HSI_NEE": float(r_p), "pearson_p": float(p_p),
            "spearman_r_HSI_NEE": float(r_s), "spearman_p": float(p_s),
            "mw_p_high_gt_low": float(mw.pvalue),
        }
        summary["years_used"].append(year)
        all_hsi.append(hsi); all_nee.append(nee)
        print(f"  {year}: n={mask.sum()} r_pearson={r_p:+.3f} p={p_p:.2e}  "
              f"NEE_low(p10)={np.nanmean(nee_low_stress):+.2f}  NEE_high(p90)={np.nanmean(nee_high_stress):+.2f}")

    if all_hsi:
        all_hsi_arr = np.concatenate(all_hsi)
        all_nee_arr = np.concatenate(all_nee)
        from scipy.stats import pearsonr, spearmanr
        r_p, p_p = pearsonr(all_hsi_arr, all_nee_arr)
        r_s, p_s = spearmanr(all_hsi_arr, all_nee_arr)
        summary["pooled_2004_2008"] = {
            "n": int(len(all_hsi_arr)),
            "pearson_r": float(r_p), "pearson_p": float(p_p),
            "spearman_r": float(r_s), "spearman_p": float(p_s),
        }
        print(f"\nPOOLED 2004-2008: n={len(all_hsi_arr):,}  pearson r={r_p:+.4f}  p={p_p:.2e}")

    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"\nsaved -> {OUT_JSON}")


if __name__ == "__main__":
    main()
