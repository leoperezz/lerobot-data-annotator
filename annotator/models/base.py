from abc import ABC, abstractmethod
from PIL import Image
from typing import Literal,Optional

class AnnotatorVLM(ABC):
    """Base class for Vision Language Model annotators."""
    
    SUPPORTED_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-robotics-er-1.5-preview",
        "gemini-3-flash-preview"
    ]

    def __init__(self,
                 model_name: str,
                 mode: Literal["video", "image"] = "video",
                 stride: Optional[int] = None,
                 fps: Optional[int] = 1):
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model_name}' is not supported. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}"
            )
        self.model_name = model_name
        self.mode = mode
        self.stride = stride
        self.fps = fps
        if self.mode == "image" and self.stride is None:
            raise ValueError("Stride is required for image mode")
        
    @abstractmethod
    def annotate(self, video_path: Optional[str], images_paths: Optional[list[str]] = None) -> str:
        """Annotate a video or images."""
        pass