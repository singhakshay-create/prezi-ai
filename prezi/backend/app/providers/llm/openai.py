from app.providers.base import LLMProvider
from app.config import settings
from openai import AsyncOpenAI
from typing import Optional


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

    def get_model_name(self) -> str:
        return f"OpenAI ({self.model})"
