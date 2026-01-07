#!/usr/bin/env python3
"""
Upload a processed LeRobot dataset to HuggingFace Hub.

This script uploads the output directory created by process_annotations.py
to a HuggingFace dataset repository.

Example usage:
    python scripts/upload_dataset.py \
        --repo-id organization-name/dataset-name \
        --new-repo-id organization-name/dataset-name-annotated \
        --branch v3.0
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo, upload_folder


def validate_dataset_structure(dataset_path: Path) -> bool:
    """
    Validates that the dataset has the required LeRobot structure.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        True if the structure is valid, False otherwise
    """
    required_dirs = ["data", "meta"]
    
    if not dataset_path.exists():
        print(f"Error: Directory {dataset_path} does not exist")
        return False
    
    for dir_name in required_dirs:
        dir_path = dataset_path / dir_name
        if not dir_path.exists():
            print(f"Warning: Directory '{dir_name}' not found")
            return False
    
    return True


def upload_dataset(repo_id: str, 
                   new_repo_id: str,
                   dataset_path: Path,
                   branch: str = "main",
                   private: bool = False,
                   commit_message: str = "Upload processed dataset with subtask annotations"):
    """
    Upload a local dataset to Hugging Face Hub.
    
    Args:
        repo_id: Original repository ID (for reference)
        new_repo_id: Destination repository ID
        dataset_path: Path to the dataset directory to upload
        branch: Branch to upload to (default: "main")
        private: Whether the repository should be private
        commit_message: Commit message for the upload
    """
    load_dotenv()
    
    # Get token from environment
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN not found in environment")
        print("\nTo set up your token:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: HF_TOKEN=your_token_here")
        print("   3. Get your token at: https://huggingface.co/settings/tokens")
        return False
    
    # Validate dataset structure
    if not validate_dataset_structure(dataset_path):
        print("Error: Dataset structure validation failed")
        return False
    
    # Initialize API
    api = HfApi(token=token)
    
    # Verify authentication
    try:
        user_info = api.whoami()
        print(f"Authenticated as: {user_info['name']}")
    except Exception as e:
        print(f"Authentication error: {e}")
        return False
    
    # Create repo if it does not exist
    print(f"Creating/verifying repo: {new_repo_id}")
    try:
        create_repo(
            repo_id=new_repo_id,
            repo_type="dataset",
            private=private,
            exist_ok=True,
            token=token
        )
        print(f"✓ Repo '{new_repo_id}' is ready")
    except Exception as e:
        print(f"Error creating repo: {e}")
        return False
    
    # Determine branches to upload to
    branches_to_upload = [branch]
    if branch != "main":
        branches_to_upload.append("main")
    
    # Create branches if they don't exist
    for branch_name in branches_to_upload:
        if branch_name != "main":
            print(f"Checking/creating branch: {branch_name}")
            try:
                api.create_branch(
                    repo_id=new_repo_id,
                    repo_type="dataset",
                    branch=branch_name,
                    token=token
                )
                print(f"✓ Branch '{branch_name}' created")
            except Exception as e:
                if "already exists" in str(e).lower() or "reference already exists" in str(e).lower():
                    print(f"Branch '{branch_name}' already exists")
                else:
                    print(f"Note: Could not create branch (might already exist): {e}")
    
    # Upload the dataset to each branch
    success = True
    for branch_name in branches_to_upload:
        print(f"\n{'='*60}")
        print(f"Uploading to branch: {branch_name}")
        print(f"{'='*60}")
        print(f"Uploading dataset to {new_repo_id}...")
        print("(This may take several minutes depending on size...)")
        
        try:
            url = upload_folder(
                folder_path=str(dataset_path),
                repo_id=new_repo_id,
                repo_type="dataset",
                commit_message=commit_message,
                revision=branch_name,
                token=token,
            )
            
            print(f"\n✓ Dataset uploaded successfully to branch '{branch_name}'!")
            print(f"   URL: {url}")
            
        except Exception as e:
            print(f"\n✗ Error uploading to branch '{branch_name}': {e}")
            import traceback
            traceback.print_exc()
            success = False
    
    if success:
        print(f"\n{'='*60}")
        print(f"All uploads completed successfully")
        print(f"{'='*60}")
        print(f"View at: https://huggingface.co/datasets/{new_repo_id}")
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Upload a processed LeRobot dataset to HuggingFace Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="Original HuggingFace repository ID (e.g., organization-name/dataset-name)"
    )
    
    parser.add_argument(
        "--new-repo-id",
        type=str,
        required=True,
        help="Destination HuggingFace repository ID for the uploaded dataset"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base data directory (default: data)"
    )
    
    parser.add_argument(
        "--output-name",
        type=str,
        default="output",
        help="Name of the output directory created by process_annotations.py (default: output)"
    )
    
    parser.add_argument(
        "--branch",
        type=str,
        default="main",
        help="Branch to upload to (default: main)"
    )
    
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make the repository private"
    )
    
    parser.add_argument(
        "--commit-message",
        type=str,
        default="Upload processed dataset with subtask annotations",
        help="Commit message for the upload"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    dataset_base_dir = Path(args.data_dir) / args.repo_id
    dataset_base_dir = dataset_base_dir.resolve()
    
    output_dataset_dir = dataset_base_dir / args.output_name
    
    if not output_dataset_dir.exists():
        parser.error(
            f"Output dataset directory not found: {output_dataset_dir}\n"
            f"Please run process_annotations.py first to create the output directory."
        )
    
    # Determine branches to upload
    branches_to_upload = [args.branch]
    if args.branch != "main":
        branches_to_upload.append("main")
    
    print("=" * 80)
    print("Uploading Dataset to HuggingFace Hub")
    print("=" * 80)
    print(f"Source: {output_dataset_dir}")
    print(f"Destination: {args.new_repo_id}")
    print(f"Branches: {', '.join(branches_to_upload)}")
    print(f"Private: {'Yes' if args.private else 'No'}")
    print()
    
    success = upload_dataset(
        repo_id=args.repo_id,
        new_repo_id=args.new_repo_id,
        dataset_path=output_dataset_dir,
        branch=args.branch,
        private=args.private,
        commit_message=args.commit_message
    )
    
    if success:
        print("\n" + "=" * 80)
        print("✓ Upload completed successfully")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("✗ Upload failed")
        print("=" * 80)
        exit(1)


if __name__ == "__main__":
    main()

