from app.providers.base import ResearchProvider
from app.models import SearchResult
from app.config import settings
from typing import List
import httpx


class PerplexityProvider(ResearchProvider):
    """Perplexity AI research provider."""

    def __init__(self):
        if not settings.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not configured")

        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using Perplexity API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Research and provide {num_results} key findings about: {query}. Include sources and citations."
                        }
                    ],
                    "return_citations": True
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")

            data = response.json()

            # Parse Perplexity response
            results = self._parse_perplexity_response(data, query)
            return results[:num_results]

    def _parse_perplexity_response(self, data: dict, query: str) -> List[SearchResult]:
        """Parse Perplexity API response into SearchResult objects."""
        results = []

        # Perplexity returns citations in the response
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        # Extract findings and match with citations
        for idx, citation in enumerate(citations[:10]):
            results.append(SearchResult(
                source=citation.get("title", f"Source {idx+1}"),
                url=citation.get("url", ""),
                snippet=citation.get("text", content[:200]),
                date=None,  # Perplexity doesn't always provide dates
                relevance_score=0.9  # High relevance for Perplexity results
            ))

        return results

    def get_provider_name(self) -> str:
        return "Perplexity AI"
