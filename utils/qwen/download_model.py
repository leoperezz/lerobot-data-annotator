#!/usr/bin/env python3
"""
Download Qwen model from HuggingFace to models/Qwen/Qwen3.5-4B.

Example usage:
    python utils/qwen/download_model.py

    python utils/qwen/download_model.py --models-dir /path/to/models
"""

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

DEFAULT_REPO_ID = "Qwen/Qwen3.5-4B"
DEFAULT_MODELS_DIR = "models"


def download_qwen_model(models_dir: Path, repo_id: str = DEFAULT_REPO_ID) -> Path:
    """
    Download Qwen model from HuggingFace.
    Saves to models_dir/Qwen/Qwen3.5-4B (preserving repo_id structure).
    """
    # Preserve org/model-name structure: Qwen/Qwen3.5-4B -> models/Qwen/Qwen3.5-4B
    output_dir = models_dir / repo_id
    print(f"Downloading model {repo_id}")
    print(f"Destination: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=repo_id,
        repo_type="model",
        local_dir=output_dir,
    )

    print(f"\n✓ Model downloaded successfully to: {output_dir}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="Download Qwen/Qwen3.5-4B model from HuggingFace to models/Qwen/Qwen3.5-4B."
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=DEFAULT_MODELS_DIR,
        help=f"Base directory for models (default: {DEFAULT_MODELS_DIR})",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=DEFAULT_REPO_ID,
        help=f"HuggingFace model repo ID (default: {DEFAULT_REPO_ID})",
    )

    args = parser.parse_args()

    download_qwen_model(
        models_dir=Path(args.models_dir),
        repo_id=args.repo_id,
    )


if __name__ == "__main__":
    main()
