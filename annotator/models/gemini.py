from annotator.models.base import AnnotatorVLM
from typing import Literal, Optional
from google import genai
from google.genai import types
import os
from typing import List
from annotator.structured import Subtasks
from annotator.prompts import PROMPT_ANNOTATE_VIDEO
from annotator.utils.tracker import UsageTracker

from dotenv import load_dotenv
load_dotenv()

class GeminiAnnotatorVLM(AnnotatorVLM):
    """Gemini Vision Language Model annotator for LeRobot datasets."""

    def __init__(self,
                 model_name: str,
                 mode: Literal["video", "image"] = "video",
                 stride: Optional[int] = None,
                 fps: Optional[int] = 1):

        super().__init__(model_name, mode, stride, fps)
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        if self.client is None:
            raise ValueError("GEMINI_API_KEY is not set")
        self.usage_tracker = UsageTracker()

    def annotate(self, video_path: Optional[str], images_paths: Optional[list[str]] = None) -> str:
        """Annotate a video or images."""
        if self.mode == "video":
            return self.annotate_video(video_path)
        elif self.mode == "image":
            return self.annotate_images(images_paths)
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

    def annotate_video(self, video_path: str, task_description: str,names_subtasks: List[str]) -> Subtasks:
        """Annotate a video."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video path {video_path} does not exist")
        

        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        
        file_ext = os.path.splitext(video_path)[1].lower()
        mime_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
        }
        mime_type = mime_type_map.get(file_ext, 'video/mp4')
        
        # Generate content with video and prompt
        model_name = f'models/{self.model_name}'
        response = self.client.models.generate_content(
            model=model_name,
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(data=video_bytes, mime_type=mime_type),
                        video_metadata=types.VideoMetadata(fps=self.fps)
                    ),
                    types.Part(text=PROMPT_ANNOTATE_VIDEO.format(task_description=task_description, subtasks=names_subtasks))
                ]
            ),
            config = {
                "response_mime_type": "application/json",
                "response_json_schema": Subtasks.model_json_schema(),
                "temperature": 0.0,
            }
        )
        self.usage_tracker.add_request()
        self.usage_tracker.add_reasoning_tokens(response.usage_metadata.prompt_token_count)
        self.usage_tracker.add_output_tokens(response.usage_metadata.candidates_token_count)
        self.usage_tracker.add_reasoning_tokens(response.usage_metadata.thoughts_token_count)

        return Subtasks.model_validate_json(response.text)

    def annotate_images(self, images_paths: list[str]) -> str:
        raise NotImplementedError("This method is not implemented")
    
    def generate_subtasks(self, video_path: Optional[str], images_paths: Optional[list[str]] = None) -> list[str]:
        raise NotImplementedError("This method is not implemented")

    def generate_subtasks_from_video(self, video_path: str) -> list[str]:
        raise NotImplementedError("This method is not implemented")

    def generate_subtasks_from_images(self, images_paths: list[str]) -> list[str]:
        raise NotImplementedError("This method is not implemented")