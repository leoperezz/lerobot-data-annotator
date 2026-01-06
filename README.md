# LeRobot Data Annotator

LeRobot Data Annotator is a tool for automatically generating temporal subtask annotations from robotic trajectory videos. It uses Vision Language Models (VLMs) to segment videos into subtasks, enabling data augmentation and fine-grained task analysis for LeRobot datasets.

## Overview

The tool processes LeRobot v3 datasets through a four-step pipeline:

1. **Download** - Fetch datasets from HuggingFace
2. **Parse** - Extract individual episodes and videos from dataset shards
3. **Configure** - Define subtasks for annotation
4. **Annotate** - Generate temporal subtask annotations using VLMs

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
    --repo-id organization-name/dataset-name
```

**Options:**
- `--repo-id`: HuggingFace repository ID (e.g., `organization-name/dataset-name`) [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--branch`: Optional branch/tag to download from

**Output Structure:**
```
data/
└── organization-name/
    └── dataset-name/
        └── lerobot-dataset/
            ├── data/
            ├── meta/
            └── videos/
```

### 2. Parse Dataset

Extract individual episodes and videos from the dataset shards:

```bash
python scripts/parse_dataset.py \
    --repo-id organization-name/dataset-name \
    --cameras observation.images.top
```

**Options:**
- `--repo-id`: HuggingFace repository ID [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--cameras`: Camera keys to extract (default: `observation.images.top`)
- `--episodes`: List of specific episode indices to process (e.g., `--episodes 0 5 10 15`)
- `--episode-range`: Range of episodes to process (e.g., `--episode-range 0 20`)

This script extracts videos and metadata for each episode into `selected_episodes/` directories.

**Expected Directory Structure After Parsing:**
```
data/
└── organization-name/
    └── dataset-name/
        ├── lerobot-dataset/
        │   ├── data/
        │   ├── meta/
        │   └── videos/
        └── selected_episodes/
            ├── episode_000000/
            │   ├── top.mp4
            │   └── metadata.json
            ├── episode_000001/
            └── ...
```

### 3. Create Subtasks Configuration

Before generating annotations, create a `subtasks.yaml` file in the dataset directory:

```bash
# Create subtasks.yaml in the dataset directory
cat > data/organization-name/dataset-name/subtasks.yaml << EOF
subtasks:
  - pick up the object A
  - place the object A in the target location
  - pick up the object B
  - place the object B in the target location
EOF
```

**Required File Structure:**
```
data/
└── organization-name/
    └── dataset-name/
        ├── lerobot-dataset/
        ├── selected_episodes/
        └── subtasks.yaml  ← Create this file
```

### 4. Generate Annotations

Generate temporal subtask annotations for episodes:

```bash
python scripts/generate_annotations.py \
    --repo-id organization-name/dataset-name \
    --model gemini-robotics-er-1.5-preview \
    --fps 2
```

**Options:**
- `--repo-id`: HuggingFace repository ID [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--model`: VLM model to use (see Supported Models below, default: `gemini-robotics-er-1.5-preview`)
- `--fps`: FPS for VLM video processing (default: 2)
- `--video-filename`: Name of video file in episode directories (default: `top.mp4`)

**Note:** The script automatically looks for `subtasks.yaml` in the dataset directory and processes all episodes in `selected_episodes/`.

**Output Structure:**
```
data/
└── organization-name/
    └── dataset-name/
        ├── lerobot-dataset/
        ├── selected_episodes/
        ├── subtasks.yaml
        └── annotations.json  ← Generated output
```

The `annotations.json` file contains:
- Temporal subtask annotations with start/end timestamps
- Episode metadata (fps, duration, frame count)
- Task descriptions
- Token usage statistics

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

## Complete Example

Here's a complete workflow example:

```bash
# 1. Download dataset
python scripts/download_dataset.py \
    --repo-id organization-name/dataset-name

# 2. Parse and extract episodes
python scripts/parse_dataset.py \
    --repo-id organization-name/dataset-name \
    --cameras observation.images.top

# 3. Create subtasks configuration
cat > data/organization-name/dataset-name/subtasks.yaml << EOF
subtasks:
  - pick up the object A
  - place the object A in the target location
EOF

# 4. Generate annotations
python scripts/generate_annotations.py \
    --repo-id organization-name/dataset-name \
    --model gemini-robotics-er-1.5-preview \
    --fps 2
```

For testing with a single episode, see `test/test_gemini_single_video.py`.

## License

Apache-2.0

