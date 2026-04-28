"""End-to-end download orchestrator.

Runs all data acquisition scripts in dependency-correct order.
Skips ones whose targets already exist (idempotent).

Day 2-7 single command:
    python scripts/run_all_downloads.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

STEPS = [
    # No-auth first (run regardless of credentials)
    ("MTBS US burn perimeters",     "download_mtbs.py"),
    ("Sentinel-2 L2A baseline",     "download_s2.py"),
    ("Tanager STAC walk",           "download_tanager.py"),
    # Auth-required
    ("EMIT Korea pre-fire",         "search_emit_korea.py"),
    ("NEON CFC + AOP",              "download_neon.py"),
    ("GEDI L4A AGB",                "download_gedi.py"),
    ("Hyperion Gwangneung 2010",    "download_hyperion.py"),
    ("산림청 임상도 WFS",          "download_imsangdo.py"),
    # Final integrity check
    ("Integrity check",             "integrity_check.py"),
]


def run_step(name: str, script: str) -> bool:
    print(f"\n{'=' * 60}")
    print(f"[{name}]  →  {script}")
    print("=" * 60)
    try:
        subprocess.run([sys.executable, str(ROOT / script)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {script} exited with {e.returncode}")
        return False


def main():
    print("PineSentry-Fire — full download orchestration")
    print(f"Steps: {len(STEPS)}")
    results = {}
    for name, script in STEPS:
        results[name] = run_step(name, script)
    print(f"\n{'=' * 60}")
    print("Summary:")
    for name, ok in results.items():
        flag = "✓" if ok else "✗"
        print(f"  {flag}  {name}")


if __name__ == "__main__":
    main()
