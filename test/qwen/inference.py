import os
import sys
from pathlib import Path

from openai import OpenAI
import dotenv
dotenv.load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from annotator.structured import Subtasks
from annotator.prompts import PROMPT_ANNOTATE_VIDEO

os.environ["CUDA_VISIBLE_DEVICES"] = "1"

# Configured by environment variables
client = OpenAI()

# Edit these to match your video and task
VIDEO_PATH = "data/NONHUMAN-RESEARCH/pick-and-place-all-fruits/selected_episodes/episode_000000/top.mp4"
TASK_DESCRIPTION = "Pick and place all fruits into the basket."
SUBTASKS = ["Reach for fruit", "Grasp fruit", "Move to basket", "Release fruit", "Return to home"]
CONTEXT = "The robot arm operates on a tabletop with multiple fruits scattered around."


def video_url_from_path(path: str) -> str:
    """Build a file:// URL for a local video. vLLM must be started with
    --allowed-local-media-path including the video's directory (or parent)."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")
    return p.as_uri()


url = video_url_from_path(VIDEO_PATH)

system_prompt = PROMPT_ANNOTATE_VIDEO.format(
    task_description=TASK_DESCRIPTION,
    subtasks=", ".join(SUBTASKS),
    context=CONTEXT,
)

messages = [
    {
        "role": "system",
        "content": system_prompt,
    },
    {
        "role": "user",
        "content": [
            {
                "type": "video_url",
                "video_url": {"url": url},
            },
            {
                "type": "text",
                "text": "Annotate the subtasks in this video.",
            },
        ],
    },
]

# Qwen3VLProcessor in vLLM does not accept mm_processor_kwargs (fps, do_sample_frames)
# in extra_body; the server uses its own video sampling. Use vLLM's --media-io-kwargs
# when starting the server if you need to control frame sampling.
chat_response = client.beta.chat.completions.parse(
    model="Qwen/Qwen3.5-4B",
    messages=messages,
    response_format=Subtasks,
    max_tokens=81920,
    temperature=1.0,
    top_p=0.95,
    presence_penalty=1.5,
    extra_body={"top_k": 20},
)

subtasks: Subtasks = chat_response.choices[0].message.parsed
print("Parsed subtasks:", subtasks)
