from pathlib import Path
from typing import Union, List
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from annotator.structured import Subtasks, Subtask, Annotation


def parse_time_to_seconds(time_str: str) -> float:
    """
    Parse a time string to seconds (float).
    
    Supports multiple formats:
    - Float string: "5.5" -> 5.5
    - MM:SS format: "00:05" -> 5.0
    - HH:MM:SS format: "01:02:03" -> 3723.0
    
    Args:
        time_str: Time string in any supported format
        
    Returns:
        Time in seconds as float
    """
    # Try to parse as float first
    try:
        return float(time_str)
    except ValueError:
        pass
    
    # Try to parse as MM:SS or HH:MM:SS format
    parts = time_str.split(':')
    if len(parts) == 2:
        # MM:SS format
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        # HH:MM:SS format
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    else:
        raise ValueError(
            f"Time string '{time_str}' is not in a supported format. "
            f"Expected: float, MM:SS, or HH:MM:SS"
        )


def create_annotated_video(
    video_path: Union[str, Path], 
    annotations: Union[Subtasks, List[Annotation]], 
    output_path: Union[str, Path], 
    fps: int = 30
) -> None:
    """
    Creates a new video with text overlays showing subtask/annotation names during their duration.

    Args:
        video_path: Path to the original video
        annotations: Either a Subtasks object or a list of Annotation objects
        output_path: Path where the annotated video will be saved
        fps: Frames per second of the video (default: 30)
    """
    # Convert Path objects to strings if needed
    video_path = str(video_path)
    output_path = str(output_path)
    
    # Load the original video
    video = VideoFileClip(video_path)
    
    # Handle both Subtasks and List[Annotation] for backward compatibility
    if isinstance(annotations, Subtasks):
        items = annotations.subtasks
    elif isinstance(annotations, list):
        items = annotations
    else:
        raise TypeError(f"annotations must be Subtasks or List[Annotation], got {type(annotations)}")
    
    # Create text clips for each annotation/subtask
    text_clips = []
    for item in items:
        # Parse start_time and end_time from strings to floats
        try:
            start_time = parse_time_to_seconds(item.start_time)
            end_time = parse_time_to_seconds(item.end_time)
        except ValueError as e:
            raise ValueError(
                f"Could not parse time values for annotation '{item.name}': "
                f"start_time='{item.start_time}', end_time='{item.end_time}'. "
                f"Error: {e}"
            )
        
        # Validate time range
        if start_time < 0:
            raise ValueError(f"start_time must be >= 0, got {start_time}")
        if end_time <= start_time:
            raise ValueError(
                f"end_time must be > start_time, got start_time={start_time}, end_time={end_time}"
            )
        if end_time > video.duration:
            print(
                f"Warning: end_time {end_time} exceeds video duration {video.duration}. "
                f"Clipping to video duration."
            )
            end_time = video.duration
        
        # Create a text clip with the annotation name
        # Using 'DejaVu-Sans' which is commonly available on Linux systems
        # or None to use the default font
        # Reduced font size from 50 to 30 for smaller text
        try:
            txt_clip = TextClip(
                text=item.name,
                font_size=30,
                color='white',
                bg_color='black',
                font='DejaVu-Sans',
                method='caption',
                size=(video.w, None)
            )
        except Exception as e:
            # Fallback: try without specifying font (use default)
            print(f"Warning: Could not use DejaVu-Sans font, using default. Error: {e}")
            txt_clip = TextClip(
                text=item.name,
                font_size=30,
                color='white',
                bg_color='black',
                method='caption',
                size=(video.w, None)
            )
        
        # Set the position (bottom of the video) and timing
        duration = end_time - start_time
        txt_clip = txt_clip.with_position(('center', 'bottom')).with_start(start_time).with_duration(duration)
        
        text_clips.append(txt_clip)
    
    # Composite the video with all text clips
    final_video = CompositeVideoClip([video] + text_clips)
    
    # Write the output video
    final_video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
    
    # Close the clips to free memory
    video.close()
    final_video.close()


def create_annotated_video_from_list(
    video_path: Union[str, Path],
    annotations: list[dict],
    output_path: Union[str, Path],
    fps: int = 30
) -> None:
    """
    Creates a new video with text overlays showing task names during their duration.
    This is a convenience function that accepts a list of dicts for backward compatibility.

    Args:
        video_path: Path to the original video
        annotations: List of dicts with start_time, end_time, and task_name
        output_path: Path where the annotated video will be saved
        fps: Frames per second of the video (default: 30)
    """
    # Convert annotations to Subtasks object
    subtask_list = [
        Subtask(
            name=ann['task_name'],
            start_time=str(ann['start_time']),
            end_time=str(ann['end_time'])
        )
        for ann in annotations
    ]
    subtasks = Subtasks(subtasks=subtask_list)
    
    # Use the main function
    create_annotated_video(video_path, subtasks, output_path, fps)

