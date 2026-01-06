#!/usr/bin/env python3
"""
Generate annotations for LeRobot episodes using Vision Language Models.

Note: A subtasks.yaml file must exist in the dataset directory
(e.g., data/organization-name/dataset-name/subtasks.yaml)

Example usage:
    python scripts/generate_annotations.py \
        --repo-id organization-name/dataset-name \
        --fps 2 \
        --model gemini-robotics-er-1.5-preview
"""

import json
import argparse
import time
from pathlib import Path
from typing import List, Optional
import yaml
from tqdm import tqdm
from annotator.models.base import AnnotatorVLM
from annotator.models.gemini import GeminiAnnotatorVLM
from annotator.utils.processors import shift_subtask_times


def load_subtasks_from_yaml(yaml_path: Path) -> List[str]:
    """Load subtasks list from a YAML file."""
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'subtasks' in data:
            return data['subtasks']
        else:
            raise ValueError("YAML file must contain a list or a dict with 'subtasks' key")


def load_metadata(episode_path: Path) -> dict:
    """Load episode metadata from JSON file."""
    with open(episode_path / "metadata.json", "r") as f:
        return json.load(f)


def save_annotations(output_path: Path, annotations: dict, usage_stats: dict):
    """Save annotations and usage statistics to JSON file."""
    output_data = {
        "annotations": annotations,
        "usage_statistics": usage_stats
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def annotate_episode_with_retry(annotator: GeminiAnnotatorVLM, 
                                video_path: Path, 
                                task_description: str,
                                subtasks: List[str],
                                max_retries: int = 3,
                                retry_delay: int = 15):
    """Annotate a single episode with retry logic."""
    for attempt in range(max_retries):
        try:
            result = annotator.annotate_video(
                video_path=str(video_path),
                task_description=task_description,
                names_subtasks=subtasks
            )
            return shift_subtask_times(result, "00:01")
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\nError on attempt {attempt + 1}/{max_retries}: {e}")
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")


def validate_subtasks_file(dataset_dir: Path) -> Path:
    """Validate that subtasks.yaml exists in the dataset directory."""
    subtasks_path = dataset_dir / "subtasks.yaml"
    
    if not subtasks_path.exists():
        raise FileNotFoundError(
            f"\nError: subtasks.yaml not found at: {subtasks_path}\n\n"
            f"The subtasks.yaml file must be created in the dataset directory.\n"
            f"Expected location: {dataset_dir}/subtasks.yaml\n\n"
            f"Example structure:\n"
            f"  data/\n"
            f"    └── organization-name/dataset-name/\n"
            f"        ├── lerobot-dataset/\n"
            f"        ├── selected_episodes/\n"
            f"        ├── subtasks.yaml  ← Create this file\n"
            f"        └── annotations.json (will be generated)\n\n"
            f"Example subtasks.yaml content:\n"
            f"  subtasks:\n"
            f"    - pick up object A\n"
            f"    - place object A in basket\n"
            f"    - return to home position\n"
        )
    
    return subtasks_path


def process_episodes(dataset_dir: Path, 
                     fps_vlm: int,
                     model_name: str,
                     video_filename: str = "top.mp4"):
    """Process all episodes in the directory and generate annotations."""
    
    subtasks_path = validate_subtasks_file(dataset_dir)
    subtasks = load_subtasks_from_yaml(subtasks_path)
    
    print(f"✓ Loaded {len(subtasks)} subtasks from: {subtasks_path}")
    for i, subtask in enumerate(subtasks, 1):
        print(f"  {i}. {subtask}")
    print()
    
    annotator = GeminiAnnotatorVLM(model_name=model_name, fps=fps_vlm)
    
    episodes_dir = dataset_dir / "selected_episodes"
    
    if not episodes_dir.exists():
        raise FileNotFoundError(
            f"\nError: selected_episodes directory not found at: {episodes_dir}\n"
            f"Please run parse_dataset.py first to extract episodes."
        )
    
    episode_dirs = sorted([d for d in episodes_dir.iterdir() if d.is_dir() and d.name.startswith("episode_")])
    
    if not episode_dirs:
        print(f"No episode directories found in {episodes_dir}")
        return
    
    output_path = dataset_dir / "annotations.json"
    annotations = {}
    
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
            annotations = existing_data.get("annotations", {})
        print(f"Loaded {len(annotations)} existing annotations from {output_path}")
    
    print(f"\nProcessing {len(episode_dirs)} episodes...")
    print(f"Model: {model_name} | FPS: {fps_vlm}")
    print(f"Output: {output_path}\n")
    
    for episode_dir in tqdm(episode_dirs, desc="Annotating episodes"):
        episode_id = episode_dir.name
        
        if episode_id in annotations:
            tqdm.write(f"Skipping {episode_id} (already annotated)")
            continue
        
        video_path = episode_dir / video_filename
        
        if not video_path.exists():
            tqdm.write(f"Warning: Video not found for {episode_id}, skipping")
            continue
        
        try:
            metadata = load_metadata(episode_dir)
            task_description = metadata.get("task_description", "Unknown task")
            
            result = annotate_episode_with_retry(
                annotator=annotator,
                video_path=video_path,
                task_description=task_description,
                subtasks=subtasks
            )
            
            annotations[episode_id] = {
                "episode_index": metadata.get("episode_index"),
                "task_index": metadata.get("task_index"),
                "task_description": task_description,
                "length_frames": metadata.get("length_frames"),
                "fps": metadata.get("fps"),
                "duration_sec": metadata.get("duration_sec"),
                "subtasks": [subtask.model_dump() for subtask in result.subtasks],
                "metadata": metadata
            }
            
            usage_stats = {
                "total_requests": annotator.usage_tracker.get_total_requests(),
                "total_tokens": annotator.usage_tracker.get_total_tokens(),
                "reasoning_tokens": annotator.usage_tracker.get_reasoning_tokens(),
                "input_tokens": annotator.usage_tracker.input_tokens,
                "output_tokens": annotator.usage_tracker.output_tokens
            }
            
            save_annotations(output_path, annotations, usage_stats)
            
        except Exception as e:
            tqdm.write(f"Error processing {episode_id}: {e}")
            continue
    
    print(f"\n✓ Processing complete!")
    print(f"Total episodes annotated: {len(annotations)}")
    print(f"Annotations saved to: {output_path}\n")
    
    annotator.usage_tracker.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Generate VLM annotations for LeRobot episodes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
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
        "--fps-vlm",
        type=int,
        default=2,
        help="Frames per second for VLM processing (default: 2)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-robotics-er-1.5-preview",
        choices=AnnotatorVLM.SUPPORTED_MODELS,
        help=f"Model to use for annotation (default: gemini-robotics-er-1.5-preview)"
    )
    
    parser.add_argument(
        "--video-filename",
        type=str,
        default="top.mp4",
        help="Name of the video file in each episode directory (default: top.mp4)"
    )
    
    args = parser.parse_args()
    
    dataset_dir = Path(args.data_dir) / args.repo_id
    dataset_dir = dataset_dir.resolve()
    
    if not dataset_dir.exists():
        parser.error(
            f"Dataset directory does not exist: {dataset_dir}\n"
            f"Please run download_dataset.py and parse_dataset.py first."
        )
    
    process_episodes(
        dataset_dir=dataset_dir,
        fps_vlm=args.fps_vlm,
        model_name=args.model,
        video_filename=args.video_filename
    )


if __name__ == "__main__":
    main()

