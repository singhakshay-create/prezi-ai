from app.providers.base import LLMProvider
from app.config import settings
from openai import AsyncOpenAI
from typing import Optional, List
import base64
import os


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider (GPT-5.2)."""

    def __init__(self, model: str = "gpt-5.2"):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generate completion using OpenAI."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        """Generate completion with image inputs using GPT-4o vision."""
        content = []
        for path in image_paths:
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_data}", "detail": "low"},
            })
        content.append({"type": "text", "text": prompt})

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def supports_vision(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return f"OpenAI ({self.model})"
