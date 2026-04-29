"""5-site bootstrap-CI summary plot for the README and submission package."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("data/hsi/v1/5site_bootstrap.png")
SUMMARY = Path("data/hsi/v1/bootstrap_summary.json")


def main():
    if not SUMMARY.exists():
        print("run bootstrap_uncertainty.py first"); return
    s = json.loads(SUMMARY.read_text())
    sites = list(s.keys())
    aucs = [s[k]["auc_mean"] for k in sites]
    lo = [s[k]["auc_q025"] for k in sites]
    hi = [s[k]["auc_q975"] for k in sites]
    lifts = [s[k]["lift_mean"] for k in sites]
    lift_lo = [s[k]["lift_q025"] for k in sites]
    lift_hi = [s[k]["lift_q975"] for k in sites]

    label_map = {
        "uiseong": "의성 Uiseong\n(EMIT 285b, KR)",
        "sancheong": "산청 Sancheong\n(EMIT 285b, KR)",
        "gangneung": "강릉 Gangneung\n(S2 13b, KR)",
        "uljin": "울진 Uljin\n(S2 13b, KR)",
        "palisades": "Palisades\n(S2 13b, US)",
    }
    color_map = {
        "uiseong": "#a50026", "sancheong": "#313695",
        "gangneung": "#1a9850", "uljin": "#984ea3", "palisades": "#fdb863",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    x = np.arange(len(sites))
    err_lo = [a - l for a, l in zip(aucs, lo)]
    err_hi = [h - a for a, h in zip(aucs, hi)]
    ax.bar(x, aucs, color=[color_map[k] for k in sites], alpha=0.85)
    ax.errorbar(x, aucs, yerr=[err_lo, err_hi], fmt="none", ecolor="black", capsize=6, capthick=1.5)
    for i, (a, l, h) in enumerate(zip(aucs, lo, hi)):
        ax.text(i, a + 0.01, f"{a:.3f}", ha="center", fontsize=9)
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.8)
    ax.axhline(0.65, color="green", linestyle=":", linewidth=0.6, alpha=0.5, label="OSF threshold 0.65")
    ax.set_xticks(x); ax.set_xticklabels([label_map[k] for k in sites], fontsize=8.5)
    ax.set_ylabel("ROC AUC")
    ax.set_title("HSI v1 — bootstrap 95% CI (n=200) across 5 fire sites")
    ax.set_ylim(0.45, 0.85)
    ax.legend(loc="upper right")

    ax = axes[1]
    err_lo_l = [a - l for a, l in zip(lifts, lift_lo)]
    err_hi_l = [h - a for a, h in zip(lifts, lift_hi)]
    ax.bar(x, lifts, color=[color_map[k] for k in sites], alpha=0.85)
    ax.errorbar(x, lifts, yerr=[err_lo_l, err_hi_l], fmt="none", ecolor="black", capsize=6, capthick=1.5)
    for i, (a, l, h) in enumerate(zip(lifts, lift_lo, lift_hi)):
        ax.text(i, a + 0.05, f"{a:.2f}x", ha="center", fontsize=9)
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels([label_map[k] for k in sites], fontsize=8.5)
    ax.set_ylabel("Top-decile lift (vs random)")
    ax.set_title("HSI v1 — top-decile lift, bootstrap 95% CI")
    ax.set_ylim(0, 3.0)

    fig.suptitle("PineSentry-Fire v1 — 5-site cross-continent generalization\n"
                 "(identical OSF-pre-registered weights)", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
