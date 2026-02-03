#!/usr/bin/env python3
"""
Process raw annotations.json and apply transformations before using in downstream tasks.

This script loads annotations.json, applies selected processors, and saves to a new file.
This allows for modular processing pipelines without modifying the original annotations.

Available processors:
  - identity: No processing, just copies the annotations to a new file
  - distribute_gaps: Distributes gaps between consecutive subtasks evenly

Example usage:
    # Apply identity processor (just copy)
    python scripts/run_processors_annotations.py \
        --repo-id organization-name/dataset-name \
        --processor identity
    
    # Apply gap distribution processor
    python scripts/run_processors_annotations.py \
        --repo-id organization-name/dataset-name \
        --processor distribute_gaps
"""

import json
import argparse
from pathlib import Path
from typing import Callable
from annotator.utils.processors import distribute_gaps_between_annotations


# Registry of available processors
PROCESSORS = {}


def register_processor(name: str):
    """Decorator to register a processor function."""
    def decorator(func: Callable):
        PROCESSORS[name] = func
        return func
    return decorator


@register_processor("identity")
def identity_processor(annotations: dict) -> dict:
    """
    Identity processor - returns annotations unchanged.
    
    This is useful when you want to create a processed annotations file
    without applying any transformations.
    
    Args:
        annotations: Raw annotations dictionary
        
    Returns:
        Same annotations dictionary unchanged
    """
    return annotations


@register_processor("distribute_gaps")
def distribute_gaps_processor(annotations: dict) -> dict:
    """
    Distribute gaps between consecutive subtasks evenly.
    
    For each episode, applies the distribute_gaps_between_annotations function
    to adjust start_frame and end_frame values to eliminate gaps.
    
    For each pair of consecutive subtasks:
    - subtask 1: [a, b]
    - subtask 2: [c, d]
    - gap = c - b
    - r = gap / 2
    - new subtask 1: [a, b + r]
    - new subtask 2: [c - r, d]
    
    Args:
        annotations: Raw annotations dictionary
        
    Returns:
        Annotations with adjusted frames
    """
    processed = {}
    
    for episode_id, episode_data in annotations.items():
        # Create a copy of episode data
        processed_episode = episode_data.copy()
        
        # Get the annotations list
        episode_annotations = episode_data.get("annotations", [])
        
        # Apply the gap distribution function
        adjusted_annotations = distribute_gaps_between_annotations(episode_annotations)
        
        # Update the episode with adjusted annotations
        processed_episode["annotations"] = adjusted_annotations
        
        processed[episode_id] = processed_episode
    
    return processed


def load_annotations(annotations_path: Path) -> dict:
    """Load annotations from JSON file."""
    if not annotations_path.exists():
        raise FileNotFoundError(
            f"\nError: annotations.json not found at: {annotations_path}\n\n"
            f"Please run generate_annotations.py first to create annotations."
        )
    
    with open(annotations_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data


def save_processed_annotations(output_path: Path, data: dict):
    """Save processed annotations to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved processed annotations to: {output_path}")


def process_annotations(annotations_path: Path, 
                       processor_name: str,
                       output_filename: str = "annotations_processed.json") -> Path:
    """
    Process annotations using the specified processor.
    
    Args:
        annotations_path: Path to input annotations.json
        processor_name: Name of the processor to use
        output_filename: Name of the output file
        
    Returns:
        Path to the processed annotations file
    """
    # Load raw annotations
    print(f"Loading annotations from: {annotations_path}")
    data = load_annotations(annotations_path)
    annotations = data.get("annotations", {})
    
    print(f"Loaded annotations for {len(annotations)} episodes")
    
    # Get the processor function
    if processor_name not in PROCESSORS:
        raise ValueError(
            f"Unknown processor: {processor_name}\n"
            f"Available processors: {', '.join(PROCESSORS.keys())}"
        )
    
    processor_func = PROCESSORS[processor_name]
    print(f"\nApplying processor: {processor_name}")
    print(f"Description: {processor_func.__doc__.strip().split(chr(10))[0]}")
    
    # Apply the processor
    processed_annotations = processor_func(annotations)
    
    # Create output data structure (preserve usage statistics if present)
    output_data = {
        "annotations": processed_annotations
    }
    
    if "usage_statistics" in data:
        output_data["usage_statistics"] = data["usage_statistics"]
    
    # Save processed annotations
    output_path = annotations_path.parent / output_filename
    save_processed_annotations(output_path, output_data)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Process annotations with various transformations",
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
        "--processor",
        type=str,
        default="distribute_gaps",
        choices=list(PROCESSORS.keys()),
        help=f"Processor to apply (default: distribute_gaps). Available: {', '.join(PROCESSORS.keys())}"
    )
    
    parser.add_argument(
        "--output-filename",
        type=str,
        default="annotations_processed.json",
        help="Name of the output file (default: annotations_processed.json)"
    )
    
    parser.add_argument(
        "--input-filename",
        type=str,
        default="annotations.json",
        help="Name of the input file (default: annotations.json)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    dataset_dir = Path(args.data_dir) / args.repo_id
    dataset_dir = dataset_dir.resolve()
    
    if not dataset_dir.exists():
        parser.error(f"Dataset directory does not exist: {dataset_dir}")
    
    annotations_path = dataset_dir / args.input_filename
    
    print("=" * 80)
    print("Processing Annotations")
    print("=" * 80)
    print(f"Dataset: {dataset_dir}")
    print(f"Input: {annotations_path.name}")
    print(f"Output: {args.output_filename}")
    print(f"Processor: {args.processor}")
    print()
    
    # Process annotations
    output_path = process_annotations(
        annotations_path=annotations_path,
        processor_name=args.processor,
        output_filename=args.output_filename
    )
    
    print("\n" + "=" * 80)
    print("✓ Processing complete!")
    print("=" * 80)
    print(f"\nProcessed annotations saved to: {output_path}\n")


if __name__ == "__main__":
    main()
