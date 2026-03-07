from pathlib import Path

from openai import OpenAI
import dotenv
dotenv.load_dotenv()

# Configured by environment variables
client = OpenAI()

# Edit these to use your local video and prompt
VIDEO_PATH = "data/NONHUMAN-RESEARCH/pick-and-place-all-fruits/selected_episodes/episode_000000/top.mp4"
PROMPT = "Summarize the video content."


def video_url_from_path(path: str) -> str:
    """Build a file:// URL for a local video. vLLM must be started with
    --allowed-local-media-path including the video's directory (or parent)."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")
    return p.as_uri()


url = video_url_from_path(VIDEO_PATH)

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "video_url",
                "video_url": {"url": url},
            },
            {
                "type": "text",
                "text": PROMPT,
            },
        ],
    }
]

# Qwen3VLProcessor in vLLM does not accept mm_processor_kwargs (fps, do_sample_frames)
# in extra_body; the server uses its own video sampling. Use vLLM's --media-io-kwargs
# when starting the server if you need to control frame sampling.
chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.5-4B",
    messages=messages,
    max_tokens=81920,
    temperature=1.0,
    top_p=0.95,
    presence_penalty=1.5,
    extra_body={"top_k": 20},
)

print("Chat response:", chat_response)
