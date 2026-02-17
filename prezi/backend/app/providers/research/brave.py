from app.providers.base import ResearchProvider
from app.models import SearchResult
from app.config import settings
from typing import List
import httpx


class BraveProvider(ResearchProvider):
    """Brave Search API provider."""

    def __init__(self):
        if not settings.BRAVE_API_KEY:
            raise ValueError("BRAVE_API_KEY not configured")

        self.api_key = settings.BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1"

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using Brave Search API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key
                },
                params={
                    "q": query,
                    "count": num_results
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Brave API error: {response.status_code} - {response.text}")

            data = response.json()
            return self._parse_brave_response(data)

    def _parse_brave_response(self, data: dict) -> List[SearchResult]:
        """Parse Brave API response into SearchResult objects."""
        results = []

        web_results = data.get("web", {}).get("results", [])

        for result in web_results:
            results.append(SearchResult(
                source=result.get("title", "Unknown"),
                url=result.get("url", ""),
                snippet=result.get("description", ""),
                date=result.get("age", None),
                relevance_score=0.85  # Brave provides quality results
            ))

        return results

    def get_provider_name(self) -> str:
        return "Brave Search"
