#!/usr/bin/env python3
"""
Utility script to parse LeRobot v3 datasets.
Maps episodes to tasks and extracts individual video segments from concatenated shards.

Example usage:
    # Process all episodes
    python utils/parse_dataset.py \\
        --input-dir input/pick-and-place-fruits-to-basket/lerobot-dataset \\
        --cameras observation.images.top observation.images.left
    
    # Process specific episodes
    python utils/parse_dataset.py \\
        --input-dir input/pick-and-place-fruits-to-basket/lerobot-dataset \\
        --cameras observation.images.top observation.images.left \\
        --episodes 0 5 10 15
    
    # Process a range of episodes
    python utils/parse_dataset.py \\
        --input-dir input/pick-and-place-fruits-to-basket/lerobot-dataset \\
        --episode-range 0 100
"""

import json
import argparse
from pathlib import Path
import pandas as pd
from moviepy import VideoFileClip
import tqdm

def parse_dataset(dataset_path: Path, cameras: list[str] = ["observation.images.top"], selected_episodes: set[int] = None):
    """
    Parse the LeRobot v3 dataset and extract individual episodes using absolute timestamps.
    """
    dataset_path = dataset_path.resolve()
    
    if dataset_path.name != "lerobot-dataset":
        raise ValueError(f"Expected dataset path to end with 'lerobot-dataset', got: {dataset_path}")
    
    output_dir = dataset_path.parent / "selected_episodes"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Parsing dataset: {dataset_path}")
    print(f"Output directory: {output_dir}")
    
    if selected_episodes is None:
        print("Processing all episodes in the dataset")
    else:
        print(f"Processing {len(selected_episodes)} selected episode(s)")
    
    info_path = dataset_path / "meta" / "info.json"
    if not info_path.exists():
        raise FileNotFoundError(f"info.json not found at {info_path}")
    
    with open(info_path, "r") as f:
        info = json.load(f)
    
    fps = info.get("fps", 30)
    print(f"Dataset FPS: {fps}")
    
    tasks_parquet = dataset_path / "meta" / "tasks.parquet"
    if not tasks_parquet.exists():
        print("Warning: tasks.parquet not found. Task descriptions will be unavailable.")
        tasks_map = {}
    else:
        tasks_df = pd.read_parquet(tasks_parquet)
        tasks_map = {}
        for idx, row in tasks_df.iterrows():
            task_idx = row.get("task_index", idx)
            
            if "task" in row:
                desc = row["task"]
            elif "task_description" in row:
                desc = row["task_description"]
            else:
                desc = str(idx) if isinstance(idx, str) else "Unknown task"
            
            tasks_map[int(task_idx)] = desc
    
    episodes_meta_dir = dataset_path / "meta" / "episodes"
    meta_files = sorted(list(episodes_meta_dir.rglob("file-*.parquet")))
    
    if not meta_files:
        print(f"No episode metadata files found in {episodes_meta_dir}")
        return

    print(f"Found {len(meta_files)} metadata shards. Processing...")

    for meta_file in meta_files:
        df = pd.read_parquet(meta_file)
        
        for _, row in tqdm.tqdm(df.iterrows(), total=len(df), desc=f"Processing {meta_file.name}"):
            try:
                if "episode_index" in row:
                    episode_index = int(row["episode_index"])
                elif "index" in row:
                    episode_index = int(row["index"])
                else:
                    continue

                if selected_episodes is not None and episode_index not in selected_episodes:
                    continue

                task_index = int(row.get("task_index", 0))
                length = int(row.get("length", 0))

                chunk_idx = row.get("meta/episodes/chunk_index", 0)
                file_idx = row.get("meta/episodes/file_index", 0)
                
                episode_output_dir = output_dir / f"episode_{episode_index:06d}"
                episode_output_dir.mkdir(parents=True, exist_ok=True)
                
                metadata = {
                    "episode_index": episode_index,
                    "task_index": task_index,
                    "task_description": tasks_map.get(task_index, "Unknown task"),
                    "length_frames": length,
                    "fps": fps,
                    "duration_sec": length / fps if length > 0 else 0
                }
                
                with open(episode_output_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                
                for cam in cameras:
                    cam_chunk = row.get(f"videos/{cam}/chunk_index", chunk_idx)
                    cam_file = row.get(f"videos/{cam}/file_index", file_idx)
                    
                    video_shard_path = dataset_path / "videos" / cam / f"chunk-{cam_chunk:03d}" / f"file-{cam_file:03d}.mp4"
                    
                    if not video_shard_path.exists():
                        print(f"Warning: Video shard {video_shard_path} not found.")
                        continue
                    
                    if f"videos/{cam}/from_timestamp" in row and f"videos/{cam}/to_timestamp" in row:
                        start_time = float(row[f"videos/{cam}/from_timestamp"])
                        end_time = float(row[f"videos/{cam}/to_timestamp"])
                    else:
                        print(f"Warning: Timestamps not found for {cam} in episode {episode_index}. Video extraction might be incorrect.")
                        continue

                    if end_time <= start_time:
                        print(f"Skipping episode {episode_index} for camera {cam}: invalid duration ({start_time} to {end_time})")
                        continue

                    try:
                        with VideoFileClip(str(video_shard_path)) as clip:
                            sub = clip.subclipped(start_time, end_time)
                            output_video_path = episode_output_dir / f"{cam.replace('observation.images.', '')}.mp4"
                            sub.write_videofile(str(output_video_path), codec="libx264", audio=False)
                    except Exception as e:
                        print(f"Error extracting video for episode {episode_index}, cam {cam}: {e}")
            except Exception as e:
                print(f"Error processing episode metadata: {e}")
                continue

def main():
    parser = argparse.ArgumentParser(description="Parse LeRobot v3 dataset and split into episodes.")
    parser.add_argument(
        "--input-dir", 
        required=True,
        help="Path to the LeRobot dataset (must end with 'lerobot-dataset')"
    )
    parser.add_argument(
        "--cameras", 
        nargs="+", 
        default=["observation.images.top"],
        help="Camera keys to extract (default: observation.images.top)"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        nargs="+",
        default=None,
        help="List of episode indices to process (e.g., --episodes 0 5 10 15). If not specified, all episodes will be processed."
    )
    parser.add_argument(
        "--episode-range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
        default=None,
        help="Range of episode indices to process (e.g., --episode-range 0 100). If not specified, all episodes will be processed."
    )
    
    args = parser.parse_args()
    
    if args.episodes is not None and args.episode_range is not None:
        parser.error("Cannot specify both --episodes and --episode-range")
    
    selected_episodes = None
    if args.episodes is not None:
        selected_episodes = set(args.episodes)
    elif args.episode_range is not None:
        start, end = args.episode_range
        selected_episodes = set(range(start, end + 1))
    
    input_path = Path(args.input_dir).resolve()
    parse_dataset(input_path, args.cameras, selected_episodes)

if __name__ == "__main__":
    main()
