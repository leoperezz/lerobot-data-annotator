from google import genai


class AnnotatorVLM:
    """Vision Language Model annotator for LeRobot datasets."""
    
    # Supported models list
    SUPPORTED_MODELS = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
    ]

    def __init__(self, model_name: str):
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model_name}' is not supported. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}"
            )
        self.model_name = model_name