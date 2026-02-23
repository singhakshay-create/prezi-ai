# Provider factory imports
from .base import LLMProvider, ResearchProvider
from .llm.claude import ClaudeProvider
from .llm.openai import OpenAIProvider
from .llm.nvidia import NvidiaProvider
from .llm.nim import NimProvider
from .llm.gemini import GeminiProvider
from .research.mock import MockResearchProvider
from .research.perplexity import PerplexityProvider
from .research.brave import BraveProvider
from .research.serp import SerpProvider
from .research.serper import SerperProvider


class ProviderFactory:
    """Factory for creating provider instances."""

    @staticmethod
    def get_llm_provider(provider_id: str) -> LLMProvider:
        """Get LLM provider instance by ID."""
        providers = {
            "claude": ClaudeProvider,
            "openai": lambda: OpenAIProvider(model="gpt-5.2"),
            "nvidia": NvidiaProvider,
            "glm5": lambda: NimProvider("zai-org/GLM-5", "NIM GLM-5"),
            "qwen": lambda: NimProvider("qwen/qwen3.5-397b-a17b", "NIM Qwen3.5-397B"),
            "deepseek": lambda: NimProvider("deepseek-ai/deepseek-v3.2", "NIM DeepSeek-V3.2"),
            "minimax": lambda: NimProvider("minimax/minimax-m2", "NIM MiniMax-M2"),
            "gemini": GeminiProvider,
            "gemini-pro": lambda: GeminiProvider(model="gemini-2.5-pro"),
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
            "serper": SerperProvider,
        }

        if provider_id not in providers:
            raise ValueError(f"Unknown research provider: {provider_id}")

        return providers[provider_id]()


__all__ = [
    "LLMProvider",
    "ResearchProvider",
    "ProviderFactory",
]
