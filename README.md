# LeRobot Data Annotator

LeRobot Data Annotator is a tool for automatically generating temporal subtask annotations from robotic trajectory videos. It uses Vision Language Models (VLMs) to segment videos into subtasks, enabling data augmentation and fine-grained task analysis for LeRobot datasets.

## Overview

The tool processes LeRobot v3 datasets through a seven-step pipeline:

1. **Download** - Fetch datasets from HuggingFace
2. **Parse** - Extract individual episodes and videos from dataset shards
3. **Configure** - Define subtasks for annotation
4. **Annotate** - Generate temporal subtask annotations using VLMs
5. **Visualize** - Generate annotated videos with subtask labels overlaid
6. **Process** - Update dataset with subtask-level task indices
7. **Upload** - Upload processed dataset to HuggingFace

## Installation

```bash
pip install -e .
```

## Setup

Create a `.env` file in the project root with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
HF_TOKEN=your_huggingface_token_here
```

**Note:** `HF_TOKEN` is required for uploading datasets to HuggingFace Hub.

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

### 5. Generate Visualizations

Generate annotated videos with subtask labels overlaid on each episode:

```bash
python scripts/generate_visualizations.py \
    --repo-id organization-name/dataset-name
```

**Options:**
- `--repo-id`: HuggingFace repository ID [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--video-filename`: Name of video file in episode directories (default: `top.mp4`)

**Note:** This script reads `annotations.json` and generates annotated videos for each episode. The annotated videos are saved in the respective episode directories within `selected_episodes/`.

**Output Structure:**
```
data/
└── organization-name/
    └── dataset-name/
        ├── lerobot-dataset/
        ├── selected_episodes/
        │   ├── episode_000000/
        │   │   ├── top.mp4
        │   │   ├── metadata.json
        │   │   └── annotated_video.mp4  ← Generated visualization
        │   ├── episode_000001/
        │   │   └── ...
        │   └── ...
        ├── subtasks.yaml
        └── annotations.json
```

Each annotated video displays subtask names as text overlays at the bottom of the video during their respective time intervals.

### 6. Process Annotations

Process annotations and update the LeRobot dataset with subtask-level task indices:

```bash
python scripts/process_annotations.py \
    --repo-id organization-name/dataset-name
```

**Options:**
- `--repo-id`: HuggingFace repository ID [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--output-name`: Name of the output directory (default: `output`)

**What this script does:**
1. Clones the `lerobot-dataset` directory to an `output` directory
2. Loads annotations from `annotations.json`
3. Builds a mapping of unique subtasks to task indices
4. Updates `meta/tasks.parquet` with all unique subtasks
5. Updates data parquet files (`data/chunk-xxx/file-xxx.parquet`) to assign correct `task_index` to each frame based on subtask annotations

**Output Structure:**
```
data/
└── organization-name/
    └── dataset-name/
        ├── lerobot-dataset/  (original)
        ├── output/  ← Processed dataset with subtask task indices
        │   ├── data/
        │   │   └── chunk-000/
        │   │       └── file-xxx.parquet  (updated with task_index)
        │   ├── meta/
        │   │   ├── tasks.parquet  (updated with all subtasks)
        │   │   └── episodes/
        │   └── videos/
        ├── selected_episodes/
        ├── subtasks.yaml
        └── annotations.json
```

**Note:** The script assigns a unique `task_index` to each unique subtask name. Frames in the data parquet files are updated to reflect the correct `task_index` based on their corresponding subtask annotation.

### 7. Upload Dataset

Upload the processed dataset to HuggingFace Hub:

```bash
python scripts/upload_dataset.py \
    --repo-id organization-name/dataset-name \
    --new-repo-id organization-name/dataset-name-annotated \
    --branch v3.0
```

**Options:**
- `--repo-id`: Original HuggingFace repository ID [Required]
- `--new-repo-id`: Destination HuggingFace repository ID [Required]
- `--data-dir`: Base data directory (default: `data`)
- `--output-name`: Name of the output directory (default: `output`)
- `--branch`: Branch to upload to (default: `main`)
- `--private`: Make the repository private (flag)
- `--commit-message`: Custom commit message for the upload

**Note:** This script requires `HF_TOKEN` in your `.env` file. It uploads the `output` directory created by `process_annotations.py` to the specified HuggingFace repository.

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
    --fps-vlm 2

# 5. Generate visualizations
python scripts/generate_visualizations.py \
    --repo-id organization-name/dataset-name

# 6. Process annotations and update dataset
python scripts/process_annotations.py \
    --repo-id organization-name/dataset-name

# 7. Upload processed dataset to HuggingFace
python scripts/upload_dataset.py \
    --repo-id organization-name/dataset-name \
    --new-repo-id organization-name/dataset-name-annotated \
    --branch v3.0
```

For testing with a single episode, see `test/test_gemini_single_video.py`.

## License

Apache-2.0

