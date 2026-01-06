import json
from pathlib import Path
from typing import Union
import argparse
import rich
from annotator.models.gemini import GeminiAnnotatorVLM
from annotator.utils.visualization import create_annotated_video
from annotator.utils.processors import shift_subtask_times

def load_metadata(episode_path: Union[str, Path]):
    episode_path = Path(episode_path)
    with open(episode_path / "metadata.json", "r") as f:
        return json.load(f)

def test_gemini_single_video(episode_path: Union[str, Path]):
    episode_path = Path(episode_path)  # Ensure it's a Path object
    metadata = load_metadata(episode_path)
    video_path = episode_path / "top.mp4"
    task_description = metadata["task_description"]
    names_subtasks = [
        "pick up the banana and put it in the basket",
        "pick up the grapes and put it in the basket",
        "pick up the strawberry and put it in the basket",
        "pick up the green pear and put it in the basket"
    ]
    annotator = GeminiAnnotatorVLM(model_name="gemini-robotics-er-1.5-preview",fps=2)
    subtasks = annotator.annotate_video(video_path=video_path, task_description=task_description, names_subtasks=names_subtasks)
    subtasks = shift_subtask_times(subtasks, "00:01")
    rich.print(subtasks)
    annotator.usage_tracker.print_summary()
    # Generate annotated video with subtitles
    output_path = episode_path / f"annotated_video_{annotator.fps}_fps.mp4"
    fps = metadata.get("fps", 30)  # Use fps from metadata if available, default to 30
    create_annotated_video(video_path=video_path, subtasks=subtasks, output_path=output_path, fps=fps)
    print(f"Annotated video saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-path", type=str, required=True)
    args = parser.parse_args()
    test_gemini_single_video(args.episode_path)
