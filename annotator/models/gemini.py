from annotator.models.base import AnnotatorVLM

class GeminiAnnotatorVLM(AnnotatorVLM):
    """Gemini Vision Language Model annotator for LeRobot datasets."""

    def __init__(self, model_name: str):
        super().__init__(model_name)

    def annotate(self, image: Image.Image) -> str:
        """Annotate an image."""
        return "Annotated image"