from app.providers.base import LLMProvider
from app.config import settings
from anthropic import AsyncAnthropic
from typing import Optional


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

    def get_model_name(self) -> str:
        return f"Claude ({self.model})"
