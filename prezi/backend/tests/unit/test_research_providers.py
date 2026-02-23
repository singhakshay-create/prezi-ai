"""Tests for research providers: BraveProvider, PerplexityProvider, SerpProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# BraveProvider
# ---------------------------------------------------------------------------

class TestBraveProvider:

    def test_raises_without_key(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = None
            from app.providers.research.brave import BraveProvider
            with pytest.raises(ValueError, match="BRAVE_API_KEY"):
                BraveProvider()

    def test_provider_name(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = "test-key"
            from app.providers.research.brave import BraveProvider
            provider = BraveProvider()
        assert provider.get_provider_name() == "Brave Search"

    def test_parse_brave_response(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = "test-key"
            from app.providers.research.brave import BraveProvider
            provider = BraveProvider()

        data = {
            "web": {
                "results": [
                    {"title": "Result A", "url": "https://a.com", "description": "Snippet A", "age": "2025-01"},
                    {"title": "Result B", "url": "https://b.com", "description": "Snippet B"},
                ]
            }
        }
        results = provider._parse_brave_response(data)
        assert len(results) == 2
        assert results[0].source == "Result A"
        assert results[0].url == "https://a.com"
        assert results[0].snippet == "Snippet A"
        assert results[0].relevance_score == 0.85

    def test_parse_brave_response_empty(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = "test-key"
            from app.providers.research.brave import BraveProvider
            provider = BraveProvider()
        results = provider._parse_brave_response({})
        assert results == []

    async def test_search_returns_results(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = "test-key"
            from app.providers.research.brave import BraveProvider
            provider = BraveProvider()

        fake_data = {
            "web": {"results": [
                {"title": "T1", "url": "https://t1.com", "description": "Snip 1"},
                {"title": "T2", "url": "https://t2.com", "description": "Snip 2"},
            ]}
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_data

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.brave.httpx.AsyncClient", return_value=mock_client):
            results = await provider.search("cloud strategy", num_results=2)

        assert len(results) == 2
        assert results[0].source == "T1"

    async def test_search_raises_on_api_error(self):
        with patch("app.providers.research.brave.settings") as ms:
            ms.BRAVE_API_KEY = "test-key"
            from app.providers.research.brave import BraveProvider
            provider = BraveProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limited"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.brave.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="Brave API error"):
                await provider.search("cloud strategy")


# ---------------------------------------------------------------------------
# PerplexityProvider
# ---------------------------------------------------------------------------

class TestPerplexityProvider:

    def test_raises_without_key(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = None
            from app.providers.research.perplexity import PerplexityProvider
            with pytest.raises(ValueError, match="PERPLEXITY_API_KEY"):
                PerplexityProvider()

    def test_provider_name(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = "test-key"
            from app.providers.research.perplexity import PerplexityProvider
            provider = PerplexityProvider()
        assert provider.get_provider_name() == "Perplexity AI"

    def test_parse_perplexity_response_with_citations(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = "test-key"
            from app.providers.research.perplexity import PerplexityProvider
            provider = PerplexityProvider()

        data = {
            "choices": [{"message": {"content": "Market is growing..."}}],
            "citations": [
                {"title": "Gartner Report", "url": "https://gartner.com/1", "text": "Cloud grew 25%"},
                {"title": "IDC Study", "url": "https://idc.com/2", "text": "Enterprise adopts fast"},
            ]
        }
        results = provider._parse_perplexity_response(data, "cloud market")
        assert len(results) == 2
        assert results[0].source == "Gartner Report"
        assert results[0].url == "https://gartner.com/1"
        assert results[0].relevance_score == 0.9

    def test_parse_perplexity_response_no_citations(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = "test-key"
            from app.providers.research.perplexity import PerplexityProvider
            provider = PerplexityProvider()

        data = {"choices": [{"message": {"content": "Some content"}}], "citations": []}
        results = provider._parse_perplexity_response(data, "query")
        assert results == []

    async def test_search_returns_results(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = "test-key"
            from app.providers.research.perplexity import PerplexityProvider
            provider = PerplexityProvider()

        fake_data = {
            "choices": [{"message": {"content": "Cloud market data"}}],
            "citations": [
                {"title": "S1", "url": "https://s1.com", "text": "Snippet one"},
                {"title": "S2", "url": "https://s2.com", "text": "Snippet two"},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_data

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.perplexity.httpx.AsyncClient", return_value=mock_client):
            results = await provider.search("cloud growth", num_results=5)

        assert len(results) == 2
        assert results[0].source == "S1"

    async def test_search_raises_on_api_error(self):
        with patch("app.providers.research.perplexity.settings") as ms:
            ms.PERPLEXITY_API_KEY = "test-key"
            from app.providers.research.perplexity import PerplexityProvider
            provider = PerplexityProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal error"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("app.providers.research.perplexity.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="Perplexity API error"):
                await provider.search("cloud growth")


# ---------------------------------------------------------------------------
# SerpProvider (Google SerpAPI)
# ---------------------------------------------------------------------------

class TestSerpProvider:

    def test_raises_without_key(self):
        with patch("app.providers.research.serp.settings") as ms:
            ms.SERP_API_KEY = None
            from app.providers.research.serp import SerpProvider
            with pytest.raises(ValueError, match="SERP_API_KEY"):
                SerpProvider()

    def test_provider_name(self):
        with patch("app.providers.research.serp.settings") as ms:
            ms.SERP_API_KEY = "test-key"
            from app.providers.research.serp import SerpProvider
            provider = SerpProvider()
        assert "Serp" in provider.get_provider_name() or "Google" in provider.get_provider_name()

    async def test_search_returns_results(self):
        """SerpProvider.search() parses organic_results via GoogleSearch mock."""
        with patch("app.providers.research.serp.settings") as ms:
            ms.SERP_API_KEY = "test-key"
            from app.providers.research.serp import SerpProvider
            provider = SerpProvider()

        fake_data = {
            "organic_results": [
                {"title": "Result 1", "link": "https://r1.com", "snippet": "Snippet 1"},
                {"title": "Result 2", "link": "https://r2.com", "snippet": "Snippet 2"},
            ]
        }
        mock_search_instance = MagicMock()
        mock_search_instance.get_dict.return_value = fake_data

        with patch("app.providers.research.serp.GoogleSearch", return_value=mock_search_instance):
            results = await provider.search("cloud market", num_results=5)

        assert len(results) == 2
        assert results[0].source == "Result 1"
        assert results[0].url == "https://r1.com"

    def test_parse_serp_response(self):
        """_parse_serp_response converts organic_results to SearchResult objects."""
        with patch("app.providers.research.serp.settings") as ms:
            ms.SERP_API_KEY = "test-key"
            from app.providers.research.serp import SerpProvider
            provider = SerpProvider()

        data = {
            "organic_results": [
                {"title": "T1", "link": "https://t1.com", "snippet": "S1", "date": "2025-01"},
            ]
        }
        results = provider._parse_serp_response(data)
        assert len(results) == 1
        assert results[0].relevance_score == 0.9

    def test_parse_serp_response_empty(self):
        with patch("app.providers.research.serp.settings") as ms:
            ms.SERP_API_KEY = "test-key"
            from app.providers.research.serp import SerpProvider
            provider = SerpProvider()
        assert provider._parse_serp_response({}) == []
