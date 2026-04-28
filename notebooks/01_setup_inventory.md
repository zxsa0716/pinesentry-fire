# Notebook 01 — Setup & STAC Inventory

> Week 0–1. Convert to .ipynb on first run. Goal: confirm 5 global Tanager scenes + EMIT Korea + 한국 wishlist 정당화.

## Cells

### Cell 1 — environment

```python
import os, sys
sys.path.insert(0, "../src")
import xarray as xr, numpy as np, pandas as pd, matplotlib.pyplot as plt
from pystac_client import Client
import earthaccess
print("Python", sys.version)
```

### Cell 2 — Tanager STAC walk

```python
!python ../scripts/download_tanager.py
```

Expected: 0 Korea scenes confirmed → 30-scene wishlist 정당화 자료. Save list of 5 global scenes for training.

### Cell 3 — EMIT 한국 검증 (v4.1 critical path)

```python
!python ../scripts/search_emit_korea.py
```

Expected (verified 2026-04-25 NASA CMR):
- 의성: 2 clear pre-fire scenes
- 산청: 5 clear pre-fire scenes
- 강릉/울진: 0 (NO-GO)

### Cell 4 — MTBS US fire perimeter

```python
!python ../scripts/download_mtbs.py
```

Confirms LA Palisades 2025-01 + Park Fire 2024-07 + Bridge/Davis perimeters available.

### Cell 5 — STATUS.md 갱신

```python
# read data/integrity_report.json and update ../STATUS.md
```

### Cell 6 — Pre-registration checkpoint

> ⚠️ Before running notebook 03 (engine training) on Korean Hero scenes, submit OSF pre-registration (OSF_PRE_REGISTRATION.md).

---

## Output to next notebook

- `data/scene_inventory.json` — list of all confirmed scenes
- `data/hero_decision.txt` — DUAL_HERO / SINGLE / FALLBACK_US
