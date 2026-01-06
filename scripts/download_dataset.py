#!/usr/bin/env python3
"""
Utility script to download a LeRobot dataset from HuggingFace.

Example usage:
    python scripts/download_dataset.py \
        --repo-id organization-name/dataset-name
    
    python scripts/download_dataset.py \
        --repo-id organization-name/dataset-name \
        --branch main \
        --data-dir data
"""

import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

def download_dataset(repo_id: str, base_data_dir: Path, branch: str | None = None):
    """
    Download a LeRobot dataset from HuggingFace.
    Preserves the full repo_id structure (organization/dataset-name) in the directory path.
    """
    output_dir = base_data_dir / repo_id / "lerobot-dataset"
    print(f"Downloading dataset {repo_id}")
    print(f"Destination: {output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=output_dir,
        revision=branch,
    )
    
    print(f"\n✓ Dataset downloaded successfully to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download a LeRobot dataset from HuggingFace.")
    parser.add_argument(
        "--repo-id", 
        type=str,
        required=True,
        help="HuggingFace repository ID (e.g., organization-name/dataset-name)"
    )
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default="data",
        help="Base data directory (default: data)"
    )
    parser.add_argument(
        "--branch", 
        type=str, 
        default=None,
        help="Branch to download from (optional)"
    )
    
    args = parser.parse_args()
    
    download_dataset(
        repo_id=args.repo_id,
        base_data_dir=Path(args.data_dir),
        branch=args.branch
    )

if __name__ == "__main__":
    main()
