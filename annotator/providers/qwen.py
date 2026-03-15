from annotator.providers.base import AnnotatorVLM
from typing import Literal, Optional, List
from pathlib import Path
from openai import OpenAI
from annotator.structured import Subtasks
from annotator.prompts import PROMPT_ANNOTATE_VIDEO
from annotator.utils.tracker import UsageTracker


class QwenAnnotatorVLM(AnnotatorVLM):
    """Qwen Vision Language Model annotator backed by a local vLLM server.

    The vLLM server must be started with --allowed-local-media-path pointing
    to the directory that contains the videos (e.g. the repo root).

    Example:
        vllm serve models/Qwen/Qwen3.5-4B \\
            --served-model-name "Qwen/Qwen3.5-4B" \\
            --port 8000 \\
            --allowed-local-media-path "$(git rev-parse --show-toplevel)"
    """

    SUPPORTED_MODELS = [
        "Qwen/Qwen3.5-4B",
        "Qwen/Qwen3.5-9B",
    ]

    def __init__(self,
                 model_name: str,
                 mode: Literal["video", "image"] = "video",
                 stride: Optional[int] = None,
                 fps: Optional[int] = 1,
                 base_url: str = "http://localhost:8000/v1",
                 api_key: str = "not-needed"):
        super().__init__(model_name, mode, stride, fps)
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.usage_tracker = UsageTracker()

    def annotate(self, video_path: Optional[str], images_paths: Optional[list[str]] = None) -> str:
        if self.mode == "video":
            return self.annotate_video(video_path)
        elif self.mode == "image":
            return self.annotate_images(images_paths)
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

    def annotate_video(self, video_path: str, task_description: str, names_subtasks: List[str], context: str = "") -> Subtasks:
        """Annotate a video using the local vLLM server.

        The video is referenced via a file:// URL so vLLM reads it directly
        from disk without uploading it over the network.
        """
        p = Path(video_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Video path {video_path} does not exist")

        video_url = p.as_uri()

        system_prompt = PROMPT_ANNOTATE_VIDEO.format(
            task_description=task_description,
            subtasks=", ".join(names_subtasks),
            context=context or "—",
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": "Annotate the subtasks in this video."},
                ],
            },
        ]

        response = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=messages,
            response_format=Subtasks,
            max_tokens=81920,
            temperature=0,
            seed=42,
        )

        self.usage_tracker.add_request()
        if response.usage:
            self.usage_tracker.add_input_tokens(response.usage.prompt_tokens or 0)
            self.usage_tracker.add_output_tokens(response.usage.completion_tokens or 0)

        return response.choices[0].message.parsed

    def annotate_images(self, images_paths: list[str]) -> str:
        raise NotImplementedError("Image mode is not implemented for QwenAnnotatorVLM")

    def generate_subtasks(self, video_path: Optional[str], images_paths: Optional[list[str]] = None) -> list[str]:
        raise NotImplementedError("This method is not implemented")

    def generate_subtasks_from_video(self, video_path: str) -> list[str]:
        raise NotImplementedError("This method is not implemented")

    def generate_subtasks_from_images(self, images_paths: list[str]) -> list[str]:
        raise NotImplementedError("This method is not implemented")
