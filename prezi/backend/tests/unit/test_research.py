"""Tests for ResearchEngine agent."""

import pytest

from app.agents.research import ResearchEngine
from app.models import Hypothesis, SearchResult, ResearchResults
from tests.conftest import DeterministicResearchProvider


def _make_hypotheses(count: int):
    return [
        Hypothesis(id=i, text=f"Hypothesis {i}", testable_claim=f"Claim {i}")
        for i in range(1, count + 1)
    ]


def _make_results(count: int, relevance: float) -> list:
    return [
        SearchResult(
            source=f"Src {i}",
            url=f"https://example.com/{i}",
            snippet=f"Snippet {i}",
            date="2025-01",
            relevance_score=relevance,
        )
        for i in range(count)
    ]


class TestValidateHypotheses:
    async def test_returns_results_per_hypothesis(self):
        """3 hypotheses → 3 HypothesisEvidence items."""
        provider = DeterministicResearchProvider()
        engine = ResearchEngine(provider)
        hypotheses = _make_hypotheses(3)

        result = await engine.validate_hypotheses(hypotheses)

        assert isinstance(result, ResearchResults)
        assert len(result.hypotheses_evidence) == 3


class TestGenerateSearchQueries:
    def test_three_queries_per_hypothesis(self):
        """Each hypothesis produces 3 search queries, first is testable_claim."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Market growth", testable_claim="Growth is 20%")

        queries = engine._generate_search_queries(hyp)

        assert len(queries) == 3
        assert queries[0] == "Growth is 20%"
        assert "market data" in queries[1]
        assert "industry analysis" in queries[2]


class TestAnalyzeEvidence:
    def test_high_relevance(self):
        """avg relevance > 0.85 → supports=True, confidence='high'."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Test", testable_claim="Claim")
        results = _make_results(5, relevance=0.95)

        evidence = engine._analyze_evidence(hyp, results)

        assert evidence.supports is True
        assert evidence.confidence == "high"

    def test_medium_relevance(self):
        """avg relevance 0.71-0.85 → supports=True, confidence='medium'."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Test", testable_claim="Claim")
        results = _make_results(5, relevance=0.80)

        evidence = engine._analyze_evidence(hyp, results)

        assert evidence.supports is True
        assert evidence.confidence == "medium"

    def test_low_relevance(self):
        """avg relevance ≤ 0.7 → supports=False, confidence='low'."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Test", testable_claim="Claim")
        results = _make_results(5, relevance=0.5)

        evidence = engine._analyze_evidence(hyp, results)

        assert evidence.supports is False
        assert evidence.confidence == "low"

    def test_empty_results(self):
        """No results → supports=False, confidence='low'."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Test", testable_claim="Claim")

        evidence = engine._analyze_evidence(hyp, [])

        assert evidence.supports is False
        assert evidence.confidence == "low"

    def test_top_10_selection(self):
        """More than 10 results → only top 10 by relevance used in evidence."""
        engine = ResearchEngine(DeterministicResearchProvider())
        hyp = Hypothesis(id=1, text="Test", testable_claim="Claim")
        results = _make_results(15, relevance=0.9)

        evidence = engine._analyze_evidence(hyp, results)

        assert len(evidence.evidence) == 10


class TestTotalSources:
    async def test_total_sources_count(self):
        """total_sources = sum of evidence counts across hypotheses."""
        provider = DeterministicResearchProvider()
        engine = ResearchEngine(provider)
        hypotheses = _make_hypotheses(2)

        result = await engine.validate_hypotheses(hypotheses)

        expected = sum(len(he.evidence) for he in result.hypotheses_evidence)
        assert result.total_sources == expected
