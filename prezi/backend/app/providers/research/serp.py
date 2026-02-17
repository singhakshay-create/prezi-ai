from app.providers.base import ResearchProvider
from app.models import SearchResult
from app.config import settings
from typing import List
from serpapi import GoogleSearch


class SerpProvider(ResearchProvider):
    """SerpAPI (Google Search) provider."""

    def __init__(self):
        if not settings.SERP_API_KEY:
            raise ValueError("SERP_API_KEY not configured")

        self.api_key = settings.SERP_API_KEY

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using SerpAPI (Google)."""
        search = GoogleSearch({
            "q": query,
            "api_key": self.api_key,
            "num": num_results
        })

        results_dict = search.get_dict()
        return self._parse_serp_response(results_dict)

    def _parse_serp_response(self, data: dict) -> List[SearchResult]:
        """Parse SerpAPI response into SearchResult objects."""
        results = []

        organic_results = data.get("organic_results", [])

        for result in organic_results:
            results.append(SearchResult(
                source=result.get("title", "Unknown"),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
                date=result.get("date", None),
                relevance_score=0.9  # High relevance for Google results
            ))

        return results

    def get_provider_name(self) -> str:
        return "SerpAPI (Google)"
