"""Deploy this repo to the HuggingFace Space at Hee-do/pinesentry-fire.

Uses the HuggingFace Hub Python API, which automatically uploads binary
files (PNG, GIF) via xet/LFS — bypassing the 'binary files rejected'
error you get from a plain `git push`.

Usage:
    pip install huggingface_hub      # one-time install
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
        from huggingface_hub.utils import EntryNotFoundError
    except ImportError:
        print("Run first:  pip install huggingface_hub", file=sys.stderr)
        sys.exit(1)

    token = get_token()
    api = HfApi(token=token)

    # === Server-side cleanup BEFORE upload ===
    # When you create a Streamlit Space on the HuggingFace UI it auto-seeds
    # a Dockerfile copied from `streamlit/streamlit-template-space`. That
    # Dockerfile takes priority over the YAML `sdk: streamlit` config and
    # will run the default spiral demo, ignoring our `streamlit_app/app.py`.
    # We delete it so HF falls back to the SDK auto-builder + our YAML.
    #
    # We also remove any accidentally-uploaded local `.env` (it can contain
    # secrets — never push it to a public Space).
    server_side_cleanup_paths = ["Dockerfile", ".env", ".envrc"]
    for p in server_side_cleanup_paths:
        try:
            api.delete_file(path_in_repo=p, repo_id=HF_REPO_ID,
                             repo_type="space",
                             commit_message=f"Remove auto-generated {p}")
            print(f"  removed pre-existing {p} from Space")
        except EntryNotFoundError:
            pass   # already absent — fine
        except Exception as e:
            print(f"  could not remove {p}: {e}")

    # === Files to NEVER upload ===
    IGNORE = [
        # Git internals
        ".git", ".git/**", ".gitignore",
        # Local-only docs / large files
        ".private", ".private/**",
        "data", "data/**",
        # Build artefacts
        "**/__pycache__", "**/__pycache__/**", "**/*.pyc",
        ".pytest_cache", ".pytest_cache/**",
        # Virtual envs
        "env", "env/**", "venv", "venv/**", ".venv", ".venv/**",
        # Heavy raw-data extensions (just in case)
        "**/*.h5", "**/*.tif", "**/*.tiff", "**/*.nc",
        # CI workflows aren't useful on the Space
        ".github", ".github/**",
        # Secrets / local-only configs (NEVER push these to a public Space)
        ".env", ".envrc", "**/.env", "**/.envrc",
        "_netrc", ".netrc", "**/_netrc", "**/.netrc",
        # Auto-seeded HF templates we replace via YAML
        "Dockerfile",
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
