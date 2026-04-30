# 8/31 Submission Checklist (User-Facing)

**Submission portal**: SurveyMonkey — Planet Tanager Open Data Competition
**Deadline**: 2026-08-31 23:59 (your local time, Asia/Seoul KST)
**D-counter**: 123 days from 2026-04-30

The research is **100% complete and frozen at git tag `v1.7`**.
What remains is administrative — the items below can be done in
~3 hours total over a weekend.

---

## Phase 1 — Pre-flight (before 8/15)

### ☐ 1. OSF DOI registration (blocking, do first)

The pre-registration document `OSF_PRE_REGISTRATION.md` is locked in git
at commit `c181cc2` (2026-04-29) but does not yet have a public OSF DOI.

Steps:
1. Go to https://osf.io and log in (create account if needed).
2. New Project → "PineSentry-Fire — Tanager 2026 pre-registration".
3. Upload the `OSF_PRE_REGISTRATION.md` file from the repo.
4. Click **"Register"** to mint a permanent DOI.
5. Replace the placeholder DOI in `CITATION.cff`:
   ```yaml
   identifiers:
     - type: doi
       value: "10.17605/OSF.IO/<NEW-ID>"   # <-- replace
   ```
6. Commit + push: `git add CITATION.cff && git commit -m "OSF DOI registered" && git push`

**Estimated time**: 30 minutes.

### ☐ 2. HuggingFace Spaces deployment (visibility, do second)

Free deployment of the Streamlit demo so reviewers can interact without
cloning the repo.

Steps:
1. Go to https://huggingface.co and log in (sign up if needed; free tier).
2. New Space → name `pinesentry-fire` → SDK = Streamlit.
3. Connect your GitHub repo `zxsa0716/pinesentry-fire`.
4. The included `Spacefile` and `streamlit_app/app.py` will autoboot.
5. Once it shows "Running", note the URL (typically
   `https://huggingface.co/spaces/<your-username>/pinesentry-fire`).
6. Add the URL to `SUBMISSION.md` Q8 alongside the GitHub link.

**Estimated time**: 1 hour (mostly waiting for the build).

### ☐ 3. Smoke-test on a fresh Colab clone

Open `colab.ipynb` in Google Colab and run all cells end-to-end. Confirm:
- The download stage finishes without 401/404 errors (you may need to
  authenticate `earthaccess.login(persist=True)` interactively).
- `python scripts/build_hsi_v1.py uiseong` produces AUC 0.747 ± 0.01.
- `python -m pytest tests/ -v` shows 9 passed.

**Estimated time**: 90 minutes (mostly download).

---

## Phase 2 — Form fill (8/20 ~ 8/30)

### ☐ 4. SurveyMonkey form Q1–Q5 (personal info)

Fill the standard contact info. Note: **Q5 is "co-authors"** — the user
indicated this can be left empty or blank-listed; do not block the
submission on co-author finalization.

### ☐ 5. Q6 — Project Description (300 words max)

Draft is in `02_idea/14_august_submission_draft.md`. Final-pass copy is
ready; just verify the headline numbers match the ones in `TABLE.md`
(no number drift between draft and current results). Specifically check:

- "AUC 0.747 (의성)" → matches `TABLE.md` Table 1 ✅
- "5-site cross-validation" → matches Table 1 ✅
- "OSF pre-registration locked at c181cc2" → matches `OSF_PRE_REGISTRATION.md` ✅

### ☐ 6. Q7 — Next Steps (100 words max)

Draft also in `02_idea/14_august_submission_draft.md`. Reference the
**30-scene Korean Tanager wishlist**: `wishlist/korea_30_scenes.geojson`
+ priority-ranked CSV `wishlist/korea_30_scenes_priority.csv` (top 3
predicted by HSI v1: 울진 송이림 0.721, 광릉 가을 단풍 0.681, 의성
일반산림 0.672).

### ☐ 7. Q8 — Project Materials Link

Paste:
- **GitHub**: https://github.com/zxsa0716/pinesentry-fire
- **HuggingFace Spaces**: (URL from Phase 1 step 2)
- (optional) OSF: (DOI from Phase 1 step 1)

---

## Phase 3 — Submit (8/30 or 8/31)

### ☐ 8. Final pre-submission check

Run from the repo root:
```bash
git status                               # clean tree, nothing uncommitted
git log v1.7 -1                          # confirms LOCK at known commit
PYTHONPATH=src python -m pytest tests/   # 9 passed
```

### ☐ 9. Click Submit on SurveyMonkey

Save the confirmation screenshot. Forward the confirmation email to
yourself for backup.

### ☐ 10. Tag the submission

```bash
git tag -a submitted-2026-08-31 -m "Submitted to Tanager 2026"
git push origin submitted-2026-08-31
```

This freezes the exact state of the submission for the record.

---

## Risk register & contingencies

| Risk | Mitigation |
|---|---|
| HuggingFace Spaces build fails | Streamlit app also runs locally; mention "free Colab reproduction" in Q8 narrative as alternative |
| Co-author missing / declines | Submit single-author; user explicitly acknowledged this is OK |
| Last-minute number-drift between draft and `TABLE.md` | The committed v1.7 numbers are immutable; only the narrative draft can change. Always cite from `TABLE.md`. |
| Internet outage on 8/31 | Submit by 8/30 (one day buffer) |
| Form question changes (SurveyMonkey rev) | Text answers in `02_idea/14_august_submission_draft.md` are flexible blocks — re-cut to fit any new question structure |

---

## What NOT to do

- **Do NOT change the OSF-pre-registered weights** (0.40 / 0.20 / 0.30 / 0.10).
  They are date-locked at commit `c181cc2`. Any change after that point
  invalidates the pre-registration claim.
- **Do NOT add more "experimental" sites** without clearly tagging them as
  post-hoc validation. The 5-site evaluation is locked.
- **Do NOT delete or revise the negative results** (PROSPECT under-
  performance, DL spatial overfit, NEE opposite-sign correlation).
  These are *strengths* of the submission, not weaknesses.

---

## After submission

The review window runs through 11/02 (winners announced).
AGU26 features the winners 12/07–12/11.

Whatever the outcome, GitHub `v1.7` and the OSF DOI are permanent
research artifacts citable from any future paper.

— *Heedo Choi · 2026-04-30*
