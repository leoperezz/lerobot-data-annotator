# LeRobot Data Annotator

LeRobot Data Annotator is a tool for automatically generating temporal subtask annotations from robotic trajectory videos. It uses Vision Language Models (VLMs) to segment videos into subtasks, enabling data augmentation and fine-grained task analysis for LeRobot datasets.

## Overview

The tool processes LeRobot v3 datasets through a three-step pipeline:

1. **Download** - Fetch datasets from HuggingFace
2. **Parse** - Extract individual episodes and videos from dataset shards
3. **Annotate** - Generate temporal subtask annotations using VLMs

## Installation

```bash
pip install -e .
```

## Setup

Create a `.env` file in the project root with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Workflow

### 1. Download Dataset

Download a LeRobot dataset from HuggingFace:

```bash
python scripts/download_dataset.py \
    --repo-id lerobot/pick-and-place-fruits-to-basket \
    --output-dir input
```

**Options:**
- `--repo-id`: HuggingFace repository ID
- `--output-dir`: Base directory to save the dataset (default: `input`)
- `--branch`: Optional branch/tag to download from

### 2. Parse Dataset

Extract individual episodes and videos from the dataset shards:

```bash
python scripts/parse_dataset.py \
    --input-dir input/pick-and-place-fruits-to-basket/lerobot-dataset \
    --cameras observation.images.top
```

**Options:**
- `--input-dir`: Path to the LeRobot dataset directory (must end with `lerobot-dataset`)
- `--cameras`: Camera keys to extract (default: `observation.images.top`)
- `--episodes`: List of specific episode indices to process (e.g., `--episodes 0 5 10 15`)
- `--episode-range`: Range of episodes to process (e.g., `--episode-range 0 20`)

This script extracts videos and metadata for each episode into `selected_episodes/` directories.

### 3. Generate Annotations

Generate temporal subtask annotations for episodes:

```bash
python scripts/generate_annotations.py \
    --input-dir input/pick-and-place-fruits-to-basket/selected_episodes \
    --model gemini-robotics-er-1.5-preview \
    --fps 2
```

**Options:**
- `--input-dir`: Directory containing episode folders
- `--model`: VLM model to use (see Supported Models below)
- `--fps`: FPS for video processing (default: 1)
- `--episodes`: Optional list of specific episodes to process

This script processes videos at scale, similar to the single-video test script, and generates annotated videos with subtask timestamps.

## Supported Models

The following Gemini models are supported:

- `gemini-2.5-flash`
- `gemini-2.5-pro`
- `gemini-robotics-er-1.5-preview`
- `gemini-3-flash-preview`

## Output

The annotation process generates:

- **Annotated videos** with subtask labels overlaid on the video timeline
- **Structured subtask data** with precise start/end timestamps for each subtask
- **Metadata** including task descriptions and episode information

## Example

See `test/test_gemini_single_video.py` for an example of processing a single episode with annotation and visualization.

## License

Apache-2.0

