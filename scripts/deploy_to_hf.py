"""Deploy this repo to the HuggingFace Space at Hee-do/pinesentry-fire.

Uses the HuggingFace Hub Python API, which automatically uploads binary
files (PNG, GIF) via xet/LFS — bypassing the 'binary files rejected'
error you get from a plain `git push`.

Usage:
    python scripts/deploy_to_hf.py

Prerequisites:
    pip install huggingface_hub
    huggingface-cli login          # paste your HF write token
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF_REPO_ID = "Hee-do/pinesentry-fire"


def main():
    from huggingface_hub import HfApi

    api = HfApi()

    # Files that should NEVER be uploaded — saves bandwidth and avoids
    # mirroring the user's local-only directories
    IGNORE = [
        # Git internals
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

    print(f"Uploading {REPO} → huggingface.co/spaces/{HF_REPO_ID}")
    print("This auto-handles LFS for binary files (PNG / GIF / etc).")
    print("Build will start automatically when upload completes.")
    print()

    api.upload_folder(
        folder_path=str(REPO),
        repo_id=HF_REPO_ID,
        repo_type="space",
        ignore_patterns=IGNORE,
        commit_message="Deploy from local clone",
    )

    print()
    print("✓ Upload complete.")
    print(f"  Watch the build:  https://huggingface.co/spaces/{HF_REPO_ID}/logs")
    print(f"  Live demo URL:    https://huggingface.co/spaces/{HF_REPO_ID}")


if __name__ == "__main__":
    main()
