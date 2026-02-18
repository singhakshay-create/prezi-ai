"""AI image generation for slide illustrations using DALL-E 3."""

import io
from typing import Optional
import httpx


class ImageGenerator:
    """
    Generates contextual illustrations for presentation slides using DALL-E 3.

    Gracefully returns None for every call when no OpenAI API key is configured,
    so the slide generator can proceed without images rather than crashing.
    """

    _STYLE_SUFFIX = (
        "Clean, professional business illustration. Modern, minimal corporate aesthetic. "
        "No text or labels in the image. Light or white background. "
        "Suitable for a management consulting presentation slide."
    )

    def __init__(self, openai_api_key: Optional[str] = None):
        self._client = None
        if openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=openai_api_key)
            except ImportError:
                pass
        # Simple in-process prompt → bytes cache to avoid duplicate API calls
        self._cache: dict = {}

    @property
    def available(self) -> bool:
        """True if a DALL-E client is configured."""
        return self._client is not None

    async def generate_image(self, prompt: str) -> Optional[io.BytesIO]:
        """
        Generate an illustration for the given prompt.

        Returns a BytesIO PNG on success, or None if unavailable or on error.
        """
        if not self._client:
            return None

        cache_key = prompt.strip().lower()
        if cache_key in self._cache:
            return io.BytesIO(self._cache[cache_key])

        try:
            full_prompt = f"{prompt.strip()}. {self._STYLE_SUFFIX}"
            response = await self._client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )
            url = response.data[0].url

            async with httpx.AsyncClient(timeout=30) as http:
                img_response = await http.get(url)
                img_response.raise_for_status()
                raw = img_response.content

            self._cache[cache_key] = raw
            return io.BytesIO(raw)

        except Exception:
            return None
