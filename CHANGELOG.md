# PineSentry-Fire Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com).

## [v1.0] — 2026-04-29 (D-124)

Initial submission-ready release for the Planet Tanager Open Data Competition 2026.

### Multi-site results (identical OSF-pre-registered weights)

| Site | Sensor | AUC | Lift@10% |
|---|---|---:|---:|
| 의성 Uiseong 2025-03 | EMIT 285b | 0.7467 | 2.30× |
| 산청 Sancheong 2025-03 | EMIT 285b | 0.6471 | 1.75× |
| 강릉 Gangneung 2023-04 | S2 13b (fallback) | 0.5487 | 1.97× |
| 울진 Uljin 2022-03 | S2 13b (fallback) | 0.5446 | 0.75× |

### Added

- HSI v1 multi-layer fusion model: pyrophilic + south_facing + firerisk_v0 + interaction.
- 19 data layers, 683 files, 156 GB total inventory.
- 8-ROI Korean peninsula atlas with HSI v1 maps via Sentinel-2 fallback.
- 30-scene Korean Tanager wishlist GeoJSON + rendered map for Q7.
- A6 weight-perturbation sensitivity analysis (±20%, n=64).
- 4×4 spatial-block CV per site.
- Spectral baseline ablation (NDVI / NDMI / NDII, both directions).
- Streamlit demo for the Q8 submission link.
- OSF pre-registration document locking v1 weights at commit c181cc2.
- Auto-updating STATUS.md via `scripts/auto_update_status.py`.
- Grand 9-panel Hero figure (`data/hsi/v1/HERO_GRAND.png`).

### Fixed

- HSM sign convention now follows Martin-StPaul 2017 (was inverted in v0).
- `percentile_normalize` returns zeros_like for degenerate inputs (no NaNs).
- `make_da` test helper infers dimensionality from input array.
- S2 fallback v1 writes the actual S2 native UTM CRS (was lying as EPSG:4326).
- `closest_pre_fire()` requires bbox-center coverage, not just intersection.
- All `build_hsi_*`, `evaluate_hsi_*`, `build_feature_stack` scripts accept SITE
  via sys.argv to prevent destructive overwrites between sites.

### Known issues

- pyhdf has no Python 3.14 wheel; MOD13Q1 NDVI anomaly + MODIS Active Fire
  density extraction deferred until conda or pyhdf release.
- ECOSIS API returns HTTP 500 — leaf spectral library data deferred.
- ESA WorldCover Uiseong tile clipped to class 0 only (no forest mask
  contribution; pyrophilic from imsangdo carries the role in v1).
- TRY DB full delivery (Korean 6 species) still pending (~6 weeks from 4/28).
- AsiaFlux GDK Tanager-era 2024-26 data still pending (1-7 days from 4/28).
- Planet API key not issued; Tanager Open Data accessed via public STAC.

### Reproducibility

- pytest 9/9 green on tests/test_hsi.py (Linux + Python 3.11 in CI).
- `requirements.txt` for pip-only environments.
- `env/environment.yml` for conda.
- `notebooks/08_one_click_reproduction.md` for Colab.
