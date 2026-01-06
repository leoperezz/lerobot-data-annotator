from abc import ABC, abstractmethod
from PIL import Image
class AnnotatorVLM(ABC):
    """Base class for Vision Language Model annotators."""

    @abstractmethod
    def annotate(self, images: list[Image.Image]) -> str:
        """Annotate an image."""
        pass