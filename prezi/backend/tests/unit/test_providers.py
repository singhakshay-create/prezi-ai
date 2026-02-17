"""Tests for ProviderFactory routing and MockResearchProvider."""

import pytest

from app.providers import ProviderFactory
from app.providers.research.mock import MockResearchProvider


class TestProviderFactory:
    def test_get_research_mock(self):
        """get_research_provider('mock') → MockResearchProvider instance."""
        provider = ProviderFactory.get_research_provider("mock")
        assert isinstance(provider, MockResearchProvider)

    def test_get_llm_unknown_raises(self):
        """get_llm_provider('gemini') → ValueError."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            ProviderFactory.get_llm_provider("gemini")

    def test_get_research_unknown_raises(self):
        """get_research_provider('google') → ValueError."""
        with pytest.raises(ValueError, match="Unknown research provider"):
            ProviderFactory.get_research_provider("google")


class TestMockResearchProvider:
    async def test_returns_correct_count(self):
        """MockResearchProvider returns requested number of results."""
        provider = MockResearchProvider()
        results = await provider.search("cloud computing", num_results=5)
        assert len(results) == 5

    async def test_capped_at_10(self):
        """num_results=20 → still max 10 results."""
        provider = MockResearchProvider()
        results = await provider.search("cloud computing", num_results=20)
        assert len(results) == 10
