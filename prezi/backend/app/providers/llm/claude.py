from app.providers.base import LLMProvider
from app.config import settings
from anthropic import AsyncAnthropic
from typing import Optional, List
import base64
import os


class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) LLM provider."""

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generate completion using Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        """Generate completion with image inputs using Claude's vision capability."""
        content = []
        for path in image_paths:
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode()
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_data},
            })
        content.append({"type": "text", "text": prompt})

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    def supports_vision(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return f"Claude ({self.model})"
