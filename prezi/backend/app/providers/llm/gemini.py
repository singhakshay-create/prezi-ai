from app.providers.base import LLMProvider
from app.config import settings
from typing import Optional, List
import base64
import os


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, model: str = "gemini-3.0-flash-preview"):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not configured")

        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._genai = genai
        self.model_name = model

    def _make_model(self, system: Optional[str] = None):
        kwargs = {"model_name": self.model_name}
        if system:
            kwargs["system_instruction"] = system
        return self._genai.GenerativeModel(**kwargs)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        model = self._make_model(system)
        config = self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = await model.generate_content_async(prompt, generation_config=config)
        return response.text

    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        from PIL import Image as PILImage

        model = self._make_model(system)
        config = self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        content = []
        for path in image_paths:
            if os.path.isfile(path):
                content.append(PILImage.open(path))
        content.append(prompt)

        response = await model.generate_content_async(content, generation_config=config)
        return response.text

    def supports_vision(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return f"Gemini ({self.model_name})"
