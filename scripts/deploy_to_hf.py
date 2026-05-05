"""Deploy this repo to the HuggingFace Space at Hee-do/pinesentry-fire.

Uses the HuggingFace Hub Python API, which automatically uploads binary
files (PNG, GIF) via xet/LFS — bypassing the 'binary files rejected'
error you get from a plain `git push`.

Usage:
    pip install huggingface_hub      # one-time install (already done)
    python scripts/deploy_to_hf.py   # asks for token, then uploads

This script is self-contained — it does NOT need `huggingface-cli login`
to be on your PATH. You can paste the token interactively, or pass it
via environment variable (`set HF_TOKEN=hf_xxxxxxxx`).
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF_REPO_ID = "Hee-do/pinesentry-fire"


def get_token() -> str:
    """Read the HF write token from $HF_TOKEN or interactive prompt."""
    token = os.environ.get("HF_TOKEN")
    if token:
        print("Using HF_TOKEN environment variable.")
        return token.strip()

    print()
    print("Paste your HuggingFace WRITE access token below.")
    print("(get one at https://huggingface.co/settings/tokens — type 'Write')")
    print("The token will not echo as you paste — that is normal.")
    try:
        token = getpass.getpass("HF write token: ")
    except (KeyboardInterrupt, EOFError):
        print("\naborted."); sys.exit(1)
    if not token.strip().startswith("hf_"):
        print("That does not look like a valid HF token (should start with 'hf_').")
        sys.exit(1)
    return token.strip()


def main():
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Run first:  pip install huggingface_hub", file=sys.stderr)
        sys.exit(1)

    token = get_token()
    api = HfApi(token=token)

    # Files that should NEVER be uploaded — saves bandwidth and avoids
    # mirroring the user's local-only directories
    IGNORE = [
        # Git internals (huggingface_hub already excludes .git, but be explicit)
        ".git", ".git/**", ".gitignore",
        # Local-only docs (PROGRESS_REPORT, SUBMISSION_CHECKLIST)
        ".private", ".private/**",
        # Raw data (huge, gitignored on GitHub too)
        "data", "data/**",
        # Build artefacts
        "**/__pycache__", "**/__pycache__/**", "**/*.pyc",
        ".pytest_cache", ".pytest_cache/**",
        # Virtual envs
        "env", "env/**", "venv", "venv/**", ".venv", ".venv/**",
        # Files we don't need on HF
        "**/*.h5", "**/*.tif", "**/*.tiff", "**/*.nc",
        # CI workflows aren't useful on the Space
        ".github", ".github/**",
    ]

    print()
    print(f"Uploading {REPO}")
    print(f"      to → huggingface.co/spaces/{HF_REPO_ID}")
    print("LFS will be applied automatically to PNG / GIF binaries.")
    print("This usually takes 1–3 minutes …")
    print()

    api.upload_folder(
        folder_path=str(REPO),
        repo_id=HF_REPO_ID,
        repo_type="space",
        ignore_patterns=IGNORE,
        commit_message="Deploy from local clone",
    )

    print()
    print("Upload complete.")
    print()
    print(f"Watch the build:  https://huggingface.co/spaces/{HF_REPO_ID}?logs=build")
    print(f"Live demo URL:    https://huggingface.co/spaces/{HF_REPO_ID}")


if __name__ == "__main__":
    main()
