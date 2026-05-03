# HuggingFace Spaces deployment guide

**Goal**: deploy the `streamlit_app/app.py` interactive demo as a
public live URL (free) so reviewers can interact without cloning
the repo. Once deployed the URL goes into Q8 of the SurveyMonkey
form alongside the GitHub link.

**Time required**: ~15 min hands-on + ~15 min build wait
**Cost**: free (HuggingFace Spaces free tier — 16 GB RAM, 2 vCPU)

---

## 1 — Prerequisites

- A GitHub account (`zxsa0716`) — already have
- A HuggingFace account (free) — sign up at https://huggingface.co/join
  if you don't already have one
- The repo `zxsa0716/pinesentry-fire` already public on GitHub ✅
- This repo already has the right config files committed:
  - `Spacefile` (HF Space metadata)
  - `streamlit_app/app.py` (the app)
  - `requirements.txt` (Python deps)
  - `examples/` (data loaded by the app)

---

## 2 — Step-by-step deployment

### 2.1 Create the Space

1. Go to https://huggingface.co/spaces and click **"+ New Space"**.
2. Fill in:
   - **Space name**: `pinesentry-fire`
   - **License**: `cc-by-4.0`
   - **Space SDK**: **Streamlit**
   - **Streamlit Space hardware**: **CPU basic** (free tier)
   - **Public** / Private: **Public**
3. Click **"Create Space"**. You now have an empty Space at
   `https://huggingface.co/spaces/<your-username>/pinesentry-fire`.

### 2.2 Connect the GitHub repo (recommended path)

The cleanest deployment is to mirror the GitHub repo into the Space.
You have two options:

**Option A — Push from local clone** (simplest):

```bash
# In your existing pinesentry-fire local clone
git remote add hf https://huggingface.co/spaces/<your-username>/pinesentry-fire
git push hf main:main
```

The Space will detect the push and start building. Watch the build
log at the URL above.

**Option B — Mirror via HF Hub web UI**:

1. On the Space page, click **"Files"** → **"Upload files"**.
2. Drag-drop the entire `pinesentry-fire/` directory.
3. Or use the HF Hub Python client:

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="C:/Users/admin/pinesentry-fire",
    repo_id="<your-username>/pinesentry-fire",
    repo_type="space",
    ignore_patterns=[".git", "data/", ".private/", "*.h5", "*.tif", "*.nc"],
)
```

### 2.3 Wait for the build (~10–15 min)

The build will install everything in `requirements.txt` (heaviest:
`prosail`, `torch`, `geopandas`). Watch logs at:
`https://huggingface.co/spaces/<your-username>/pinesentry-fire/logs`

When the build succeeds, the Space shows **"Running"** in green and
you can interact with the demo at:
`https://huggingface.co/spaces/<your-username>/pinesentry-fire`

### 2.4 Verify

The 10 tabs should all render content. Specifically:
- **Hero figures** tab: 4 PNGs visible
- **5-site results** tab: dataframe shows 5 rows with AUC values
- **Statistical battery**: 4 PNGs + GEE odds-ratio table
- **Trait inversion**: 6-row table including v2.8 PyTorch result
- **Pre-fire temporal**: animated GIF plays
- **Q7 wishlist**: top-7 ranking visible

---

## 3 — Common issues and fixes

| Problem | Fix |
|---|---|
| Build fails: `ERROR: Could not find a version that satisfies the requirement torch` | HF Spaces auto-pins `torch==X` from `requirements.txt`. Either pin to a known-good version (`torch==2.1.0`) or use `--index-url https://download.pytorch.org/whl/cpu` in the requirements line |
| Build fails: `prosail not found` | Confirm `prosail` is in `requirements.txt` (it is, in v1.9) |
| App loads but figures are missing | The Space build did not include `examples/`. Check `.gitignore` did not exclude `examples/` (it doesn't, in v1.9) |
| Korean characters render as boxes | Add a Korean font in `Spacefile`'s `app_file_dependencies`, e.g. `apt: fonts-nanum`. The current submission renders Korean glyphs in matplotlib output PNGs but inside text labels they may show as boxes |
| OOM (Out of Memory) | Comment out the heaviest tabs (Statistical battery has 5 PNGs; consider lazy loading) |
| 503 / Container exit | HF free tier sleeps after inactivity; first visitor wakes it up in ~30s |

---

## 4 — Add the live URL to Q8 of the SurveyMonkey form

Once the Space is running, paste the URL into the Q8 field alongside
the GitHub link. Suggested format:

```
Project Materials Link:

GitHub:                  https://github.com/zxsa0716/pinesentry-fire
HuggingFace Spaces (live): https://huggingface.co/spaces/<your-username>/pinesentry-fire
OSF DOI:                 (after Phase 1 step 1 in SUBMISSION_CHECKLIST.md)
```

---

## 5 — Optional: persistence config

If you want the Space to NOT sleep on inactivity (for the review window
between 8/31 and 11/02), upgrade the Space to **CPU upgraded**
(non-free, ~$0.05 / hour). The free tier is fine for the submission
itself — judges will wake it up on first visit.

---

## 6 — `Spacefile` reference

This repo's `Spacefile` is already correct:

```yaml
title: PineSentry-Fire
emoji: 🌲🔥
colorFrom: red
colorTo: yellow
sdk: streamlit
sdk_version: 1.30.0
app_file: streamlit_app/app.py
pinned: false
license: cc-by-4.0
```

Do not modify unless you intend a different SDK or app entry point.
