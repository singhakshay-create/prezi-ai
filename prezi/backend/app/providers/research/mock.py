from app.providers.base import ResearchProvider
from app.models import SearchResult
from typing import List
import random


class MockResearchProvider(ResearchProvider):
    """Mock research provider for testing and demo purposes."""

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Generate mock search results."""
        mock_sources = [
            "McKinsey Global Institute",
            "BCG Henderson Institute",
            "Bain & Company Insights",
            "Deloitte Insights",
            "PwC Research",
            "Gartner Research",
            "Forrester",
            "Harvard Business Review",
            "MIT Sloan Management Review",
            "Financial Times"
        ]

        results = []
        for i in range(min(num_results, 10)):
            source = random.choice(mock_sources)
            results.append(SearchResult(
                source=source,
                url=f"https://example.com/research/{i+1}",
                snippet=f"Mock research finding related to '{query}': {self._generate_snippet(query)}",
                date="2025-01",
                relevance_score=random.uniform(0.7, 1.0)
            ))

        return results

    def _generate_snippet(self, query: str) -> str:
        """Generate a realistic-looking snippet."""
        templates = [
            f"Recent analysis suggests that {query} is experiencing significant growth, with market indicators showing positive trends.",
            f"Industry experts note that {query} presents both opportunities and challenges for market entrants.",
            f"Data from 2024-2025 indicates that {query} is becoming increasingly important in the competitive landscape.",
            f"Strategic considerations for {query} include market timing, competitive positioning, and regulatory factors.",
            f"Research shows that {query} could generate substantial value creation opportunities over the next 3-5 years."
        ]
        return random.choice(templates)

    def get_provider_name(self) -> str:
        return "Mock Research Provider"
