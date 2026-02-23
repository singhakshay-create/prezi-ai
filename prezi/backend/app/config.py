from pydantic_settings import BaseSettings
from typing import List, Optional

PLACEHOLDER_PREFIXES = ("your_", "sk-ant-xxx", "sk-proj-xxx", "nvapi-xxx")


def _is_real_key(value: Optional[str]) -> bool:
    """Check if an API key is a real key, not a placeholder."""
    if not value:
        return False
    v = value.strip()
    if not v:
        return False
    for prefix in PLACEHOLDER_PREFIXES:
        if v.startswith(prefix):
            return False
    return True


class Settings(BaseSettings):
    # LLM API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Research API Keys
    PERPLEXITY_API_KEY: Optional[str] = None
    BRAVE_API_KEY: Optional[str] = None
    SERP_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./data/prezi.db"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def available_llm_providers(self) -> List[dict]:
        """Return list of available LLM providers with metadata."""
        providers = []

        if _is_real_key(self.ANTHROPIC_API_KEY):
            providers.append({
                "id": "claude",
                "name": "Claude 3.5 Sonnet",
                "available": True,
                "description": "Best for structured reasoning and analysis"
            })

        if _is_real_key(self.OPENAI_API_KEY):
            providers.append({
                "id": "openai",
                "name": "GPT-5.2",
                "available": True,
                "description": "Latest OpenAI reasoning model"
            })

        if _is_real_key(self.NVIDIA_API_KEY):
            providers.append({
                "id": "nvidia",
                "name": "Kimi K2 (thinking)",
                "available": True,
                "description": "Extended chain-of-thought reasoning"
            })
            providers.append({
                "id": "glm5",
                "name": "GLM-5",
                "available": True,
                "description": "ZhipuAI GLM-5 via Nvidia NIM"
            })
            providers.append({
                "id": "qwen",
                "name": "Qwen3.5-397B",
                "available": True,
                "description": "Qwen3.5 MoE 397B via Nvidia NIM"
            })
            providers.append({
                "id": "deepseek",
                "name": "DeepSeek-V3.2",
                "available": True,
                "description": "DeepSeek-V3.2 via Nvidia NIM"
            })
            providers.append({
                "id": "minimax",
                "name": "MiniMax-M2",
                "available": True,
                "description": "MiniMax-M2 via Nvidia NIM"
            })

        # Add unavailable providers (grayed out in UI)
        if not _is_real_key(self.ANTHROPIC_API_KEY):
            providers.append({
                "id": "claude",
                "name": "Claude 3.5 Sonnet",
                "available": False,
                "description": "Requires ANTHROPIC_API_KEY"
            })

        if not _is_real_key(self.OPENAI_API_KEY):
            providers.append({
                "id": "openai",
                "name": "GPT-5.2",
                "available": False,
                "description": "Requires OPENAI_API_KEY"
            })

        if not _is_real_key(self.NVIDIA_API_KEY):
            providers.append({
                "id": "nvidia",
                "name": "Kimi K2 / GLM-5 / Qwen3.5 / DeepSeek-V3.2 / MiniMax-M2",
                "available": False,
                "description": "Requires NVIDIA_API_KEY"
            })

        if _is_real_key(self.GOOGLE_API_KEY):
            providers.append({
                "id": "gemini",
                "name": "Gemini 3.0 Flash Preview",
                "available": True,
                "description": "Fast multimodal model with vision support"
            })
            providers.append({
                "id": "gemini-pro",
                "name": "Gemini 2.5 Pro",
                "available": True,
                "description": "Most capable Gemini model"
            })
        else:
            providers.append({
                "id": "gemini",
                "name": "Gemini 3.0 Flash Preview / 2.5 Pro",
                "available": False,
                "description": "Requires GOOGLE_API_KEY"
            })

        return providers

    @property
    def available_research_providers(self) -> List[dict]:
        """Return list of available research providers with metadata."""
        providers = [
            {
                "id": "mock",
                "name": "Mock Data (Demo)",
                "available": True,
                "description": "Fast mock data for testing"
            }
        ]

        if _is_real_key(self.PERPLEXITY_API_KEY):
            providers.append({
                "id": "perplexity",
                "name": "Perplexity",
                "available": True,
                "description": "AI-powered research with citations"
            })

        if _is_real_key(self.BRAVE_API_KEY):
            providers.append({
                "id": "brave",
                "name": "Brave Search",
                "available": True,
                "description": "Privacy-focused search"
            })

        if _is_real_key(self.SERP_API_KEY):
            providers.append({
                "id": "serp",
                "name": "SerpAPI (Google)",
                "available": True,
                "description": "Google search results"
            })

        if _is_real_key(self.SERPER_API_KEY):
            providers.append({
                "id": "serper",
                "name": "Serper (Google Search)",
                "available": True,
                "description": "Google search via Serper.dev"
            })

        return providers


settings = Settings()
