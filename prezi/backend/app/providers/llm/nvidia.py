from app.providers.base import LLMProvider
from app.config import settings
from openai import AsyncOpenAI
from typing import Optional


class NvidiaProvider(LLMProvider):
    """Nvidia (Kimi K2) LLM provider using OpenAI-compatible API."""

    def __init__(self):
        if not settings.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY not configured")

        self.client = AsyncOpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.model = "moonshotai/kimi-k2-instruct"

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generate completion using Nvidia Kimi K2."""
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

    def get_model_name(self) -> str:
        return f"Nvidia ({self.model})"
