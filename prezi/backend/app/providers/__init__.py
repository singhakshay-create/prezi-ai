# Provider factory imports
from .base import LLMProvider, ResearchProvider
from .llm.claude import ClaudeProvider
from .llm.openai import OpenAIProvider
from .llm.nvidia import NvidiaProvider
from .research.mock import MockResearchProvider
from .research.perplexity import PerplexityProvider
from .research.brave import BraveProvider
from .research.serp import SerpProvider


class ProviderFactory:
    """Factory for creating provider instances."""

    @staticmethod
    def get_llm_provider(provider_id: str) -> LLMProvider:
        """Get LLM provider instance by ID."""
        providers = {
            "claude": ClaudeProvider,
            "openai": lambda: OpenAIProvider(model="gpt-5.2"),
            "nvidia": NvidiaProvider,
        }

        if provider_id not in providers:
            raise ValueError(f"Unknown LLM provider: {provider_id}")

        provider_class = providers[provider_id]
        return provider_class()

    @staticmethod
    def get_research_provider(provider_id: str) -> ResearchProvider:
        """Get research provider instance by ID."""
        providers = {
            "mock": MockResearchProvider,
            "perplexity": PerplexityProvider,
            "brave": BraveProvider,
            "serp": SerpProvider,
        }

        if provider_id not in providers:
            raise ValueError(f"Unknown research provider: {provider_id}")

        return providers[provider_id]()


__all__ = [
    "LLMProvider",
    "ResearchProvider",
    "ProviderFactory",
]
