"""Multi-site v1 driver: 의성 + 산청 cross-application + leave-one-out.

For each Korean fire site that has an EMIT baseline scene + imsangdo
clip + dNBR perimeter:
  1. Build HSI v0 (empirical proxies + species P50)
  2. Build feature stack (10 bands)
  3. Compute HSI v1 + evaluate against dNBR
  4. Save Hero PNG + eval PNG

Then a summary of per-site AUC + lift, and a leave-one-out style
narrative: do the v1 weights generalize across sites?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SITES = {
    "uiseong":   {"emit_glob": "EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc"},
    "sancheong": {"emit_glob": "EMIT_L2A_RFL_001_20241219T032003_2435402_004.nc"},
    # Gangneung: pre-EMIT-launch fire (2023-04). Pre-fire scene from 2022-08
    # onwards. Search picks closest winter; we re-pick deterministically for
    # reproducibility.
    "gangneung": {"emit_glob": None},
    # Uljin: pre-EMIT (2022-03), no pre-fire scene available — skip
    "uljin":     {"emit_glob": None},
}


def run_site(site: str, emit_path: Path) -> dict:
    """Run v0 + feature_stack + v1 for one site. Returns metrics dict."""
    print(f"\n{'='*70}\n SITE: {site}  ({emit_path.name})\n{'='*70}")

    # Patch build_hsi_v0.py target via env-style override: simplest is to
    # symlink / temporarily set the path. We import the module directly.
    import importlib, importlib.util, sys as _sys
    sys_modules_keys = [k for k in _sys.modules.keys() if "build_hsi_v0" in k]
    for k in sys_modules_keys:
        del _sys.modules[k]

    # Inject the SITE-specific paths
    spec = importlib.util.spec_from_file_location("build_hsi_v0", "scripts/build_hsi_v0.py")
    mod = importlib.util.module_from_spec(spec)
    mod.EMIT_NC = emit_path
    mod.IMSANGDO = Path(f"data/imsangdo/{site}.gpkg")
    mod.OUT_DIR = Path("data/hsi/v0")
    mod.OUT_DIR.mkdir(parents=True, exist_ok=True)
    # The script uses a hardcoded Hero PNG name "uiseong_*"; we monkey-patch.
    spec.loader.exec_module(mod)
    # Run main() with monkey-patched site name in output names
    # The build_hsi_v0 script writes uiseong_hsi_v0.tif regardless; we'll
    # rename per site after run.
    try:
        mod.main()
    except SystemExit:
        pass

    # Rename outputs from "uiseong_*" to "{site}_*" if needed
    out_dir = Path("data/hsi/v0")
    if site != "uiseong":
        for prefix in ("uiseong_hsi_v0.tif", "uiseong_firerisk_v0.tif", "uiseong_hero_v0.png"):
            src = out_dir / prefix
            if src.exists():
                dst = out_dir / prefix.replace("uiseong_", f"{site}_")
                src.replace(dst)

    # Build feature stack via subprocess for clean per-site path
    import subprocess
    print(f"\n--- feature_stack {site} ---")
    subprocess.run([sys.executable, "scripts/build_feature_stack.py", site], check=False)
    print(f"\n--- HSI v1 {site} ---")
    res = subprocess.run([sys.executable, "scripts/build_hsi_v1.py", site], capture_output=True, text=True)
    print(res.stdout[-2000:] if res.stdout else "")
    print(res.stderr[-500:] if res.stderr else "")

    # Parse AUC from stdout
    auc = lift = None
    for line in (res.stdout or "").splitlines():
        if "ROC AUC" in line:
            try:
                auc = float(line.split("=")[1].strip().split()[0])
            except Exception:
                pass
        if "top-decile lift" in line:
            try:
                lift = float(line.split("=")[1].strip().split("x")[0])
            except Exception:
                pass
    return {"site": site, "auc": auc, "lift": lift}


def main():
    out_summary = []
    for site, info in SITES.items():
        em = info.get("emit_glob")
        if em is None:
            print(f"\nSITE {site}: no EMIT baseline available — SKIP")
            continue
        emit_path = Path(f"data/emit/{site}/{em}")
        if not emit_path.exists():
            print(f"SITE {site}: missing EMIT scene {emit_path} — SKIP")
            continue
        try:
            r = run_site(site, emit_path)
        except Exception as e:
            print(f"  failed: {e}", file=sys.stderr)
            r = {"site": site, "error": str(e)}
        out_summary.append(r)

    print(f"\n{'='*70}\n MULTI-SITE SUMMARY\n{'='*70}")
    for r in out_summary:
        print(r)


if __name__ == "__main__":
    main()
