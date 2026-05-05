"""Grand Tour animated GIF — every key result of PineSentry-Fire in one
scrolling reel. ~16 frames, ~1.2s each, totals ~20s.

Story arc:
  Frame 1   — title card
  Frames 2-6 — each of the 5 cross-validation sites (HSI v1 raster + perimeter)
  Frame 7   — bootstrap 95 % ROC envelope (5-site)
  Frame 8   — 6-panel methods comparison
  Frame 9   — A1-A4 leave-one-out
  Frame 10  — Permutation null
  Frame 11  — Boyce monotonic incidence
  Frame 12  — Calibration before/after isotonic
  Frame 13  — Pre-fire signal at Sancheong (T-1.5 mo)
  Frame 14  — Trait inversion variants ladder
  Frame 15  — Q7 30-scene wishlist priority map
  Frame 16  — closing card with key numbers

Output:
  examples/figures/00_grand_tour_animation.gif
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

OUT = Path("examples/figures/00_grand_tour_animation.gif")

# Use a Korean-capable font in case any glyphs slip through
plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

EX_FIG = Path("examples/figures")
EX_TAB = Path("examples/tables")
EX_MAP = Path("examples/maps")

SITES_HSI = {
    "uiseong":   ("Uiseong (Korea)",       "AUC 0.747",   "EMIT 285b"),
    "sancheong": ("Sancheong (Korea)",     "AUC 0.647",   "EMIT 285b"),
    "gangneung": ("Gangneung (Korea)",     "AUC 0.549",   "Sentinel-2 13b"),
    "uljin":     ("Uljin (Korea)",         "AUC 0.545",   "Sentinel-2 13b"),
    "palisades": ("LA Palisades (US)",     "AUC 0.678",   "Sentinel-2 13b"),
}


def render_title_card():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=110)
    ax.set_facecolor("#fafafa")
    ax.text(0.5, 0.78, "PineSentry-Fire", ha="center", fontsize=46,
             fontweight="bold", color="#a50026", transform=ax.transAxes)
    ax.text(0.5, 0.66,
             "Pre-fire Hydraulic Stress Index for pine forests",
             ha="center", fontsize=22, color="#444", transform=ax.transAxes)
    ax.text(0.5, 0.56,
             "Cross-validated on 5 fires, 2 continents,\n"
             "with identical pre-registered weights",
             ha="center", fontsize=16, color="#666", transform=ax.transAxes)
    ax.text(0.5, 0.34,
             "Tanager Open Data Competition 2026  |  Code & Scripts",
             ha="center", fontsize=14, color="#a50026",
             transform=ax.transAxes, fontweight="bold")
    ax.text(0.5, 0.24,
             "Heedo Choi  -  Kookmin University",
             ha="center", fontsize=12, color="#666",
             transform=ax.transAxes)
    ax.text(0.5, 0.10,
             "→  github.com/zxsa0716/pinesentry-fire",
             ha="center", fontsize=11, color="#1a4d8a",
             transform=ax.transAxes, style="italic")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    return _fig_to_array(fig)


def render_image_card(img_path: Path, title: str, subtitle: str = "",
                       footer: str = "", color: str = "#a50026"):
    """Card showing an existing PNG with title + subtitle overlay."""
    fig, ax = plt.subplots(figsize=(14, 8), dpi=110)
    ax.set_facecolor("white")
    if img_path.exists():
        img = Image.open(img_path).convert("RGB")
        ax.imshow(np.array(img), zorder=1)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

    fig.suptitle(title, fontsize=20, fontweight="bold", color=color, y=0.99)
    if subtitle:
        fig.text(0.5, 0.93, subtitle, ha="center", fontsize=13, color="#444")
    if footer:
        fig.text(0.5, 0.04, footer, ha="center", fontsize=11, color="#666",
                  style="italic")
    return _fig_to_array(fig)


def render_site_card(site: str, label: str, auc_label: str, sensor_label: str):
    """Per-site card combining HSI eval figure + summary stats."""
    eval_pngs = {
        "uiseong":   "13_uiseong_eval.png",
        "sancheong": "14_sancheong_eval.png",
        "palisades": "15_palisades_eval.png",
    }
    fname = eval_pngs.get(site)
    if not fname:
        # Fallback: use bootstrap chart for the S2-fallback Korean sites
        fname = "05_bootstrap_95CI.png"
    return render_image_card(
        EX_FIG / fname,
        title=f"Site: {label}",
        subtitle=f"{auc_label}  |  sensor: {sensor_label}  |  same pre-registered HSI v1 weights",
        footer="HSI v1 = 0.40 pyrophilic + 0.20 south_facing + 0.30 firerisk_v0 "
                "+ 0.10 (pyro x south)",
        color="#a50026",
    )


def render_closing_card():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=110)
    ax.set_facecolor("#fafafa")
    ax.text(0.5, 0.88, "Key takeaways", ha="center", fontsize=30,
             fontweight="bold", color="#a50026", transform=ax.transAxes)
    bullets = [
        ("AUC 0.747",            "Uiseong, EMIT 285-band, n = 25,804 burn pixels"),
        ("Cross-continent",       "Korea-tuned weights work on US chaparral (Palisades AUC 0.678)"),
        ("p < 1/1000",           "all 5 sites pass the permutation null"),
        ("Pre-registered weights", "git commit c181cc2, 2026-04-29 (before any test result)"),
        ("6-week pre-fire signal", "EMIT detects pyrophilic stress at Sancheong T-1.5 mo, Δ +0.146"),
        ("30-scene Q7 wishlist",   "answers 'where would Tanager add information?' quantitatively"),
    ]
    for i, (head, body) in enumerate(bullets):
        y = 0.78 - i * 0.105
        ax.text(0.06, y, "•", fontsize=20, color="#a50026",
                 transform=ax.transAxes, fontweight="bold")
        ax.text(0.10, y, head + ": ", fontsize=14, fontweight="bold",
                 color="#a50026", transform=ax.transAxes)
        ax.text(0.40, y, body, fontsize=13, color="#222",
                 transform=ax.transAxes)
    ax.text(0.5, 0.07,
             "github.com/zxsa0716/pinesentry-fire   |   CC-BY-4.0",
             ha="center", fontsize=12, color="#1a4d8a", style="italic",
             transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    return _fig_to_array(fig)


def _fig_to_array(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", facecolor="white", bbox_inches="tight",
                 dpi=fig.dpi)
    plt.close(fig)
    buf.seek(0)
    return np.array(Image.open(buf).convert("RGB"))


def main():
    frames: list[np.ndarray] = []
    durations: list[int] = []   # ms per frame

    # 1. Title (longer hold)
    frames.append(render_title_card());                                     durations.append(2400)

    # 2-6. Per-site cards (5 sites)
    for site, (label, auc, sensor) in SITES_HSI.items():
        frames.append(render_site_card(site, label, auc, sensor));          durations.append(1800)

    # 7. ROC envelope (the headline rigour figure)
    frames.append(render_image_card(
        EX_FIG / "03_HERO_roc_envelope_5site.png",
        "5-site ROC + 95 % bootstrap envelope",
        "Uncertainty visualised as a SHAPE, not just a CI number",
        "n_bootstrap = 200 per site"));                                     durations.append(2200)

    # 8. Methods comparison
    frames.append(render_image_card(
        EX_FIG / "02_HERO_methods_6panel.png",
        "Methods comparison — every benchmark side-by-side",
        "(a) ladder · (b) cross-site weight transfer · (c) GEE / Moran "
        "(d) permutation · (e) Boyce · (f) per-species AUC", ""));         durations.append(2400)

    # 9. A1-A4 ablation
    frames.append(render_image_card(
        EX_FIG / "08_A1_A4_ablations.png",
        "A1-A4 leave-one-out ablation",
        "Removing pyrophilic drops Uiseong AUC by 0.108 (largest)",
        "Removing south_facing drops Sancheong AUC by 0.110"));            durations.append(2200)

    # 10. Permutation null
    frames.append(render_image_card(
        EX_FIG / "06_permutation_null_N1000.png",
        "Permutation null distributions (N = 1000)",
        "Red line = observed AUC, grey = null AUC under random shuffles",
        "All 5 sites: p < 1/1000"));                                       durations.append(2200)

    # 11. Boyce
    frames.append(render_image_card(
        EX_FIG / "07_boyce_index.png",
        "Boyce continuous index — monotonic burn-incidence vs HSI bin",
        "Uiseong rho = 1.000 (textbook monotonic)",
        "Sancheong rho = 0.943"));                                         durations.append(2200)

    # 12. Calibration
    frames.append(render_image_card(
        EX_FIG / "10_calibration_isotonic.png",
        "Calibration: Brier scores raw vs isotonic-regression",
        "Uiseong Brier 0.32 → 0.07 after calibration",
        "All 5 sites improved post-calibration"));                         durations.append(2000)

    # 13. Pre-fire signal — the 6-week-ahead lead time claim
    frames.append(render_image_card(
        EX_FIG / "16_sancheong_pre_fire_signal.png",
        "Pre-fire signal at Sancheong (T - 1.5 mo)",
        "EMIT detects pyrophilic stress 6 weeks before the 2026-03 ignition",
        "Δ firerisk = +0.146  |  n = 13,323 burn pixels  |  p ≈ 0"));     durations.append(2400)

    # 14. Trait inversion variants
    fig, ax = plt.subplots(figsize=(14, 8), dpi=110)
    methods = ["v0\nNDII/NDVI\nempirical", "v1\nfull HSI\n(pre-registered)",
               "v2\nPROSPECT-D\nleaf MLP", "v2.5\nPROSAIL\ncanopy MLP",
               "v2.7\nscipy\nfinite-diff", "v2.8\nPyTorch\nautograd"]
    aucs = [0.697, 0.747, 0.648, 0.608, 0.500, 0.683]
    cols = ["#fc8d59", "#a50026", "#74add1", "#74add1", "#aaaaaa", "#1a9850"]
    bars = ax.bar(methods, aucs, color=cols, edgecolor="black", linewidth=0.6)
    for b, v in zip(bars, aucs):
        ax.text(b.get_x() + b.get_width()/2, v + 0.01, f"{v:.3f}",
                 ha="center", fontsize=12, fontweight="bold")
    ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.7)
    ax.set_ylabel("ROC AUC (Uiseong)", fontsize=13)
    ax.set_ylim(0.45, 0.83)
    ax.set_title("Trait-inversion variants — pre-registered HSI v1 wins",
                  fontsize=18, fontweight="bold", color="#a50026", pad=14)
    ax.text(0.5, -0.16,
             "Pure radiative-transfer inversion under-performs empirical NDII proxy "
             "on conifer fire-risk.\nv2.8 PyTorch autograd recovers a real signal that "
             "v2.7 finite-difference scipy misses.",
             ha="center", fontsize=11, color="#444", transform=ax.transAxes)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    frames.append(_fig_to_array(fig));                                     durations.append(2400)

    # 15. Wishlist priority map
    if (EX_MAP / "korea_30_scene_wishlist.png").exists():
        frames.append(render_image_card(
            EX_MAP / "korea_30_scene_wishlist.png",
            "Q7: 30-scene Korean Tanager wishlist",
            "Each scene scored quantitatively by predicted HSI v1",
            "Top 3: Uljin matsutake forest 0.721 / Gwangneung autumn senescence 0.681 / Uiseong general forest 0.672"));    durations.append(2400)

    # 16. Closing card (longer hold)
    frames.append(render_closing_card());                                   durations.append(3500)

    # Pad all frames to the largest shape
    max_h = max(f.shape[0] for f in frames)
    max_w = max(f.shape[1] for f in frames)
    padded = []
    for f in frames:
        h, w, _ = f.shape
        canvas = np.full((max_h, max_w, 3), 255, dtype=np.uint8)
        oy = (max_h - h) // 2
        ox = (max_w - w) // 2
        canvas[oy:oy+h, ox:ox+w] = f
        padded.append(canvas)

    import imageio.v3 as iio
    OUT.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(OUT, padded, duration=durations, loop=0, plugin="pillow")
    print(f"saved -> {OUT} ({OUT.stat().st_size/1e6:.2f} MB, {len(padded)} frames)")


if __name__ == "__main__":
    main()
