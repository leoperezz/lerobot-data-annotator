#!/usr/bin/env python3
"""
Utility script to download a LeRobot dataset from HuggingFace.

Example usage:
    python utils/download_dataset.py \
        --repo-id lerobot/pick-and-place-fruits-to-basket \
        --output-dir input
    
    python utils/download_dataset.py \
        --repo-id lerobot/pick-and-place-fruits-to-basket \
        --output-dir input \
        --branch main
"""

import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

def download_dataset(repo_id: str, base_output_dir: Path, branch: str | None = None):
    """
    Download a LeRobot dataset from HuggingFace using its URL.
    """
    dataset_name = repo_id.split("/")[-1]
    output_dir = base_output_dir / dataset_name / "lerobot-dataset"
    print(f"Downloading dataset {repo_id} to {output_dir}...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=output_dir,
        revision=branch,
    )
    
    print(f"Dataset downloaded successfully to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download a LeRobot dataset from HuggingFace.")
    parser.add_argument(
        "--repo-id", 
        type=str,
        help="HuggingFace repository ID"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="input",
        help="Base local directory to save the dataset"
    )
    parser.add_argument(
        "--branch", 
        type=str, 
        default=None,
        help="Branch to download the dataset from"
    )
    
    args = parser.parse_args()
    
    download_dataset(repo_id=args.repo_id,
                    base_output_dir=Path(args.output_dir),
                    branch=args.branch)

if __name__ == "__main__":
    main()
