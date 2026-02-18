from abc import ABC, abstractmethod
from typing import List, Optional
from app.models import SearchResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate text completion from the LLM.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        pass

    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        """Generate text from a prompt + images. Falls back to text-only if not overridden."""
        return await self.generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens)

    def supports_vision(self) -> bool:
        """Return True if this provider has a real vision implementation."""
        return False

    def get_model_name(self) -> str:
        """Get the model name for this provider."""
        return self.__class__.__name__


class ResearchProvider(ABC):
    """Abstract base class for research/search providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10
    ) -> List[SearchResult]:
        """
        Search for information related to the query.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        pass

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.__class__.__name__
