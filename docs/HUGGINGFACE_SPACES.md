# HuggingFace Spaces deployment guide

**Goal**: deploy the Streamlit demo at
`https://huggingface.co/spaces/Hee-do/pinesentry-fire` so reviewers can
interact without cloning anything.

**Time required**: ~10 minutes hands-on + ~5–10 minutes build wait
**Cost**: free (HuggingFace Spaces free tier — 16 GB RAM, 2 vCPU)

> The Space is already created at
> [huggingface.co/spaces/Hee-do/pinesentry-fire](https://huggingface.co/spaces/Hee-do/pinesentry-fire).
> What follows is how to push the local repo into it.

---

## 1 — Prerequisites

You already have:
- A GitHub account (`zxsa0716`) with the repo public
- A HuggingFace Space created at `Hee-do/pinesentry-fire` (Streamlit SDK)

You still need:
- A **HuggingFace write-access token** (one-time setup)
- Git installed locally

### Get a HuggingFace access token (1 minute)

1. Go to https://huggingface.co/settings/tokens
2. Click **"+ New token"**
3. Token type: **Write** (must be Write, not Read)
4. Name: `pinesentry-push` (any name)
5. Click **Generate**, then **copy the token** (`hf_...` long string)

You will paste this when Git asks for your password during the push.

---

## 2 — Push your local repo to the Space (3 minutes)

In a terminal at the local clone (`C:/Users/admin/pinesentry-fire`):

```bash
# 1) Add the Space as a second git remote (do this ONCE only)
git remote add hf https://huggingface.co/spaces/Hee-do/pinesentry-fire

# 2) Push the entire 'main' branch to that remote
git push hf main:main
```

When Git prompts:

```
Username for 'https://huggingface.co': Hee-do
Password for 'https://Hee-do@huggingface.co': hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

(Paste the access token from step 1 — it acts as your password. Git won't echo it as you type.)

If the first push fails because the Space already has commits (an empty
init commit from when you created it), do:

```bash
git pull hf main --allow-unrelated-histories     # merge any auto-init commit
# resolve any conflict in README.md if Git asks
git push hf main:main
```

After a successful push you will see your repo files appear in the
Space's **Files** tab on the website.

---

## 3 — Watch the build (5–10 minutes)

Open
`https://huggingface.co/spaces/Hee-do/pinesentry-fire/logs`
in your browser. You will see HF run, in order:

1. `Cloning the repo` (~10 s)
2. `pip install -r requirements.txt` (~1–2 minutes — only streamlit + numpy)
3. `streamlit run streamlit_app/app.py` (~30 s)

Once the log shows
`Streamlit app running on http://localhost:8501`,
the Space is **Running** (green badge top-right).

The live URL is
`https://huggingface.co/spaces/Hee-do/pinesentry-fire`
— that is what goes into Q8 of the SurveyMonkey form.

---

## 4 — Verify the running Space

The 10 tabs of the demo should all render content. Specifically check:
- **Hero figures** tab: 4 PNGs visible (Grand Tour GIF, methods, ROC envelope, dual hero)
- **5-site results** tab: 5 rows in the AUC dataframe
- **Statistical battery** tab: 4 PNGs + GEE odds-ratio table populated
- **Trait inversion** tab: 6-row table including v2.8 PyTorch row
- **Pre-fire temporal** tab: pre-fire signal figure visible
- **Q7 wishlist** tab: top-7 ranking visible

---

## 5 — Why the README has a YAML block at the top

HF Spaces reads the deployment config from a YAML frontmatter at the top
of `README.md`:

```yaml
---
title: PineSentry-Fire
emoji: 🌲
colorFrom: red
colorTo: orange
sdk: streamlit
sdk_version: 1.30.0
app_file: streamlit_app/app.py
pinned: false
license: cc-by-4.0
short_description: Pre-fire Hydraulic Stress Index for Korean pine forests
---
```

GitHub renders the block as plain text (it doesn't break GitHub's display)
but HF treats it as configuration. **Do not edit the YAML block** — the
deployment depends on the exact `app_file` path.

---

## 6 — Why `requirements.txt` is small (only `streamlit`, `numpy`)

The Streamlit app only reads PNG / JSON files in `examples/` — it doesn't
re-run any of the modeling pipeline. So we keep `requirements.txt`
minimal to make the Space build fast.

The full pipeline deps (rasterio, geopandas, prosail, torch, etc.) are
in `requirements-pipeline.txt` — used only when reproducing the analysis
locally or in Colab.

---

## 7 — Common issues

| Problem | Fix |
|---|---|
| `git push hf main:main` says "Authentication failed" | Token must be **Write**-scoped, not Read. Regenerate at huggingface.co/settings/tokens. |
| Build log: `streamlit app file not found` | Confirm `streamlit_app/app.py` exists in the pushed branch and `app_file` matches in YAML. |
| Build log: requires `xxx` not satisfied | The slim `requirements.txt` should not have heavy deps. If you accidentally pushed `requirements-pipeline.txt` content, restore the slim version. |
| Space shows empty page | Click the menu top-right → **Restart Space**. First boot can hang; restart fixes it 90 % of the time. |
| Korean characters render as boxes | Already fixed: site labels and figures use English only. |
| 503 / Container exit | HF free-tier sleeps after inactivity. First visitor wakes it in ~30 s — totally normal. |

---

## 8 — Adding the live URL to Q8 of the SurveyMonkey form

Final Q8 field text (paste exactly):

```
GitHub repository (case study + code):
  https://github.com/zxsa0716/pinesentry-fire

Live interactive demo (HuggingFace Spaces):
  https://huggingface.co/spaces/Hee-do/pinesentry-fire

1-click reproduction (Google Colab):
  https://colab.research.google.com/github/zxsa0716/pinesentry-fire/blob/main/colab.ipynb
```

---

## 9 — Updating the Space after future GitHub commits

After every meaningful GitHub commit you want mirrored, just run:

```bash
git push hf main:main
```

It re-uploads the changed files and HF auto-rebuilds the Space.
