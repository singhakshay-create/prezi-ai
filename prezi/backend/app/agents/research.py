from app.providers.base import ResearchProvider
from app.models import Hypothesis, HypothesisEvidence, ResearchResults, SearchResult
from typing import List


class ResearchEngine:
    """Conducts hypothesis-driven research using search providers."""

    def __init__(self, research_provider: ResearchProvider):
        self.provider = research_provider

    async def validate_hypotheses(self, hypotheses: List[Hypothesis]) -> ResearchResults:
        """Research and validate each hypothesis."""
        hypotheses_evidence = []

        for hypothesis in hypotheses:
            # Generate search queries for this hypothesis
            queries = self._generate_search_queries(hypothesis)

            # Collect evidence from multiple searches
            all_results = []
            for query in queries:
                results = await self.provider.search(query, num_results=5)
                all_results.extend(results)

            # Analyze evidence and determine support/confidence
            evidence_analysis = self._analyze_evidence(hypothesis, all_results)
            hypotheses_evidence.append(evidence_analysis)

        return ResearchResults(
            hypotheses_evidence=hypotheses_evidence,
            total_sources=sum(len(he.evidence) for he in hypotheses_evidence)
        )

    def _generate_search_queries(self, hypothesis: Hypothesis) -> List[str]:
        """Generate multiple search queries to test a hypothesis."""
        queries = [
            hypothesis.testable_claim,
            f"{hypothesis.text} market data",
            f"{hypothesis.text} industry analysis"
        ]
        return queries

    def _analyze_evidence(self, hypothesis: Hypothesis, results: List[SearchResult]) -> HypothesisEvidence:
        """Analyze search results to determine if they support the hypothesis."""

        # Sort by relevance and take top results
        sorted_results = sorted(results, key=lambda r: r.relevance_score, reverse=True)
        top_results = sorted_results[:10]

        # Simple heuristic: if we have good evidence, hypothesis is supported
        # In a real system, this would use LLM to analyze evidence
        avg_relevance = sum(r.relevance_score for r in top_results) / len(top_results) if top_results else 0

        supports = avg_relevance > 0.7
        confidence = "high" if avg_relevance > 0.85 else "medium" if avg_relevance > 0.7 else "low"

        conclusion = f"{'Supported' if supports else 'Insufficient evidence'} - Found {len(top_results)} relevant sources"

        return HypothesisEvidence(
            hypothesis_id=hypothesis.id,
            evidence=top_results,
            supports=supports,
            confidence=confidence,
            conclusion=conclusion
        )
