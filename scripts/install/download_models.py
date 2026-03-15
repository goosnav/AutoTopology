#!/usr/bin/env python3
"""Download model GGUF files from HuggingFace for AutoTopology.

Usage:
    python scripts/install/download_models.py
    python scripts/install/download_models.py --models-dir ./my_models
    python scripts/install/download_models.py --model-name moondream2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Model registry – add new models here
# ---------------------------------------------------------------------------
MODEL_REGISTRY: dict[str, dict] = {
    "moondream2": {
        "repo_id": "ggml-org/moondream2-20250414-GGUF",
        "subdir": "moondream2",
        "patterns": [
            "*mmproj*",       # multimodal projector file(s)
            "*.gguf",         # main model GGUF(s)
        ],
        "description": "Moondream2 vision-language model (GGUF)",
    },
}

# Default models directory relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_DIR = _PROJECT_ROOT / "models"


def _ensure_huggingface_hub() -> None:
    """Check that huggingface_hub is installed, print instructions if not."""
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        print(
            "\n[ERROR] The 'huggingface_hub' package is required but not installed.\n"
            "Install it with:\n\n"
            "    pip install huggingface-hub\n"
        )
        sys.exit(1)


def _list_repo_files(repo_id: str) -> list[str]:
    """Return all filenames in a HuggingFace repo."""
    from huggingface_hub import list_repo_files

    return list(list_repo_files(repo_id))


def _match_files(all_files: list[str], patterns: list[str]) -> list[str]:
    """Filter *all_files* against a list of glob-style patterns."""
    import fnmatch

    matched: list[str] = []
    for pattern in patterns:
        for fname in all_files:
            if fnmatch.fnmatch(fname, pattern) and fname not in matched:
                matched.append(fname)
    return matched


def download_model(
    model_name: str,
    models_dir: Path,
    *,
    force: bool = False,
) -> bool:
    """Download a single model's files. Returns True on success."""
    from huggingface_hub import hf_hub_download

    if model_name not in MODEL_REGISTRY:
        print(f"\n[ERROR] Unknown model '{model_name}'.")
        print(f"Available models: {', '.join(MODEL_REGISTRY)}")
        return False

    spec = MODEL_REGISTRY[model_name]
    repo_id: str = spec["repo_id"]
    dest_dir = models_dir / spec["subdir"]
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Model      : {model_name}")
    print(f"Repository : https://huggingface.co/{repo_id}")
    print(f"Destination: {dest_dir}")
    print(f"{'='*60}\n")

    # ---- Enumerate remote files -------------------------------------------
    print("[1/3] Listing files in repository ...")
    try:
        all_files = _list_repo_files(repo_id)
    except Exception as exc:
        print(f"\n[ERROR] Could not list files in '{repo_id}':\n  {exc}")
        _print_failure_help(repo_id)
        return False

    targets = _match_files(all_files, spec["patterns"])
    if not targets:
        print(f"\n[ERROR] No files matched patterns {spec['patterns']} in '{repo_id}'.")
        print("Available files:")
        for f in sorted(all_files):
            print(f"  - {f}")
        return False

    print(f"  Found {len(targets)} file(s) to download:")
    for t in targets:
        print(f"    - {t}")

    # ---- Download ---------------------------------------------------------
    print(f"\n[2/3] Downloading to {dest_dir} ...")
    downloaded: list[Path] = []
    for filename in targets:
        local_path = dest_dir / Path(filename).name
        if local_path.exists() and not force:
            print(f"  [SKIP] {local_path.name} (already exists, use --force to re-download)")
            downloaded.append(local_path)
            continue
        print(f"  Downloading {filename} ...")
        try:
            cached = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(dest_dir),
                local_dir_use_symlinks=False,
            )
            downloaded.append(Path(cached))
            print(f"    -> {cached}")
        except Exception as exc:
            print(f"\n[ERROR] Failed to download '{filename}':\n  {exc}")
            _print_failure_help(repo_id)
            return False

    # ---- Verify -----------------------------------------------------------
    print(f"\n[3/3] Verifying downloaded files ...")
    all_ok = True
    for dl in downloaded:
        exists = dl.exists()
        size_mb = dl.stat().st_size / (1024 * 1024) if exists else 0
        status = f"OK ({size_mb:,.1f} MB)" if exists else "MISSING"
        print(f"  {dl.name}: {status}")
        if not exists:
            all_ok = False

    if all_ok:
        print(f"\n[SUCCESS] All files for '{model_name}' downloaded to {dest_dir}\n")
    else:
        print(f"\n[WARNING] Some files are missing – check errors above.\n")

    return all_ok


def _print_failure_help(repo_id: str) -> None:
    """Print actionable troubleshooting steps after a download failure."""
    print(
        "\n--- Troubleshooting ---\n"
        "1. Check your internet connection.\n"
        f"2. Verify the repo exists: https://huggingface.co/{repo_id}\n"
        "3. If the repo is gated/private, authenticate:\n"
        "       huggingface-cli login\n"
        "4. Ensure 'huggingface_hub' is up-to-date:\n"
        "       pip install --upgrade huggingface-hub\n"
        "5. If behind a proxy, set HTTPS_PROXY / HTTP_PROXY env vars.\n"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download GGUF model files for AutoTopology.",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help=f"Root directory for downloaded models (default: {DEFAULT_MODELS_DIR})",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="moondream2",
        choices=list(MODEL_REGISTRY),
        help="Which model to download (default: moondream2)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist locally.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_models",
        help="List available models and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.list_models:
        print("Available models:")
        for name, spec in MODEL_REGISTRY.items():
            print(f"  {name:20s} - {spec['description']}")
        sys.exit(0)

    _ensure_huggingface_hub()

    ok = download_model(
        model_name=args.model_name,
        models_dir=args.models_dir,
        force=args.force,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
