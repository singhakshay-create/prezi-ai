"""Tests for ProviderFactory routing and MockResearchProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers import ProviderFactory
from app.providers.research.mock import MockResearchProvider
from app.providers.research.serper import SerperProvider
from app.providers.llm.nvidia import NvidiaProvider


class TestProviderFactory:
    def test_get_research_mock(self):
        """get_research_provider('mock') → MockResearchProvider instance."""
        provider = ProviderFactory.get_research_provider("mock")
        assert isinstance(provider, MockResearchProvider)

    def test_get_llm_unknown_raises(self):
        """get_llm_provider with unknown id → ValueError."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            ProviderFactory.get_llm_provider("nonexistent_provider_xyz")

    def test_get_research_unknown_raises(self):
        """get_research_provider('google') → ValueError."""
        with pytest.raises(ValueError, match="Unknown research provider"):
            ProviderFactory.get_research_provider("google")


class TestSerperProvider:
    def test_provider_name(self):
        """get_provider_name() returns 'Serper'."""
        with patch("app.providers.research.serper.settings") as mock_settings:
            mock_settings.SERPER_API_KEY = "test-key-123"
            provider = SerperProvider()
            assert provider.get_provider_name() == "Serper"

    def test_raises_without_api_key(self):
        """SerperProvider raises ValueError when SERPER_API_KEY is not set."""
        with patch("app.providers.research.serper.settings") as mock_settings:
            mock_settings.SERPER_API_KEY = None
            with pytest.raises(ValueError, match="SERPER_API_KEY not configured"):
                SerperProvider()

    async def test_returns_results(self):
        """search() parses organic results into SearchResult objects."""
        fake_response = {
            "organic": [
                {"title": "Result One", "link": "https://example.com/1", "snippet": "Snippet one", "date": "2025-01-01", "position": 1},
                {"title": "Result Two", "link": "https://example.com/2", "snippet": "Snippet two", "date": None, "position": 2},
                {"title": "Result Three", "link": "https://example.com/3", "snippet": "Snippet three", "position": 3},
            ]
        }

        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.serper.settings") as mock_settings:
            mock_settings.SERPER_API_KEY = "test-key-123"
            provider = SerperProvider()

            with patch("httpx.AsyncClient", return_value=mock_client):
                results = await provider.search("cloud computing", num_results=3)

        assert len(results) == 3
        assert results[0].source == "Result One"
        assert results[0].url == "https://example.com/1"
        assert results[0].snippet == "Snippet one"
        assert results[0].date == "2025-01-01"
        assert results[1].source == "Result Two"

    async def test_relevance_scoring(self):
        """Position 1 → 0.95, position 5 → 0.75."""
        fake_response = {
            "organic": [
                {"title": "A", "link": "https://a.com", "snippet": "a", "position": 1},
                {"title": "B", "link": "https://b.com", "snippet": "b", "position": 5},
            ]
        }

        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_response
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.serper.settings") as mock_settings:
            mock_settings.SERPER_API_KEY = "test-key-123"
            provider = SerperProvider()

            with patch("httpx.AsyncClient", return_value=mock_client):
                results = await provider.search("test query", num_results=10)

        assert results[0].relevance_score == pytest.approx(0.95)
        assert results[1].relevance_score == pytest.approx(0.75)


class TestNvidiaProvider:
    def _make_provider(self):
        with patch("app.providers.llm.nvidia.settings") as mock_settings:
            mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
            with patch("app.providers.llm.nvidia.AsyncOpenAI"):
                provider = NvidiaProvider()
        return provider

    async def _fake_stream(self, *content_chunks):
        """Helper: yield fake stream chunks as an async generator."""
        for text in content_chunks:
            chunk = MagicMock()
            chunk.choices[0].delta.content = text
            yield chunk

    async def test_thinking_tags_stripped(self):
        """Response with <think>...</think> block returns only the final answer."""
        with patch("app.providers.llm.nvidia.settings") as mock_settings:
            mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                return_value=self._fake_stream("<think>\nreasoning\n</think>\nFinal answer")
            )

            with patch("app.providers.llm.nvidia.AsyncOpenAI", return_value=mock_client):
                provider = NvidiaProvider()
                result = await provider.generate("test prompt")

        assert result == "Final answer"

    async def test_no_thinking_tags(self):
        """Response without <think> tags is returned as-is."""
        with patch("app.providers.llm.nvidia.settings") as mock_settings:
            mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                return_value=self._fake_stream("Plain response text")
            )

            with patch("app.providers.llm.nvidia.AsyncOpenAI", return_value=mock_client):
                provider = NvidiaProvider()
                result = await provider.generate("test prompt")

        assert result == "Plain response text"

    async def test_extra_body_passed(self):
        """API call includes extra_body with enable_thinking=True."""
        with patch("app.providers.llm.nvidia.settings") as mock_settings:
            mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "answer"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.nvidia.AsyncOpenAI", return_value=mock_client):
                provider = NvidiaProvider()
                await provider.generate("test prompt")

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": True}}


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
