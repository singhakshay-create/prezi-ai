"""Shared fixtures for Prezi AI backend tests."""

import json
import os
import pytest
from typing import List, Optional
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Storyline,
    SCQAFramework,
    Hypothesis,
    SearchResult,
    HypothesisEvidence,
    ResearchResults,
    QualityScore,
)
from app.providers.base import LLMProvider, ResearchProvider
from app.database import Base, Job, get_db


# ---------------------------------------------------------------------------
# Mock Providers
# ---------------------------------------------------------------------------


class MockLLMProvider(LLMProvider):
    """Concrete LLMProvider subclass that returns configurable responses."""

    def __init__(self, response: str = "{}"):
        self.response = response
        self.calls: list = []

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "system": system,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    async def generate_with_vision(
        self,
        prompt: str,
        image_paths,
        system=None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "image_paths": image_paths,
                "system": system,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    def supports_vision(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return "MockLLM"


class DeterministicResearchProvider(ResearchProvider):
    """Research provider that returns fixed, predictable SearchResult lists."""

    def __init__(self, results: Optional[List[SearchResult]] = None):
        self._results = results or self._default_results()

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        return self._results[:num_results]

    def get_provider_name(self) -> str:
        return "DeterministicResearch"

    @staticmethod
    def _default_results() -> List[SearchResult]:
        return [
            SearchResult(
                source=f"Source {i}",
                url=f"https://example.com/{i}",
                snippet=f"Finding number {i} with relevant data.",
                date="2025-01",
                relevance_score=0.95 - i * 0.05,
            )
            for i in range(10)
        ]


# ---------------------------------------------------------------------------
# Sample JSON strings (as an LLM would return them)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_storyline_json() -> str:
    """Valid JSON matching expected LLM output for StorylineGenerator."""
    return json.dumps(
        {
            "scqa": {
                "situation": "The global cloud computing market is growing at 20% CAGR.",
                "complication": "Enterprise adoption is slowing due to security and cost concerns.",
                "question": "How can cloud providers accelerate enterprise adoption?",
                "answer": "Focus on hybrid solutions, strengthen security posture, and offer flexible pricing.",
            },
            "governing_thought": "Hybrid cloud with strong security is the key to unlocking enterprise growth.",
            "key_line": "Three strategic pillars can drive 30% faster adoption.",
            "hypotheses": [
                {
                    "id": 1,
                    "text": "Hybrid cloud solutions drive faster enterprise adoption",
                    "testable_claim": "Enterprises with hybrid strategies grow cloud spending 2x faster",
                },
                {
                    "id": 2,
                    "text": "Security certifications reduce procurement cycle time",
                    "testable_claim": "SOC2/ISO certified providers close deals 40% faster",
                },
                {
                    "id": 3,
                    "text": "Flexible pricing improves conversion from trial to paid",
                    "testable_claim": "Pay-as-you-go models convert 3x better than annual contracts",
                },
            ],
        }
    )


@pytest.fixture
def sample_quality_json() -> str:
    """Valid JSON matching expected LLM output for QualityChecker."""
    return json.dumps(
        {
            "slide_logic": 85,
            "mece_structure": 80,
            "so_what": 90,
            "data_quality": 85,
            "chart_accuracy": 80,
            "visual_consistency": 85,
            "suggestions": [
                "Add more quantitative evidence",
                "Strengthen the MECE structure",
            ],
        }
    )


# ---------------------------------------------------------------------------
# Pre-built domain model instances
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_storyline() -> Storyline:
    return Storyline(
        scqa=SCQAFramework(
            situation="The global cloud computing market is growing at 20% CAGR.",
            complication="Enterprise adoption is slowing due to security and cost concerns.",
            question="How can cloud providers accelerate enterprise adoption?",
            answer="Focus on hybrid solutions, strengthen security posture, and offer flexible pricing.",
        ),
        governing_thought="Hybrid cloud with strong security is the key to unlocking enterprise growth.",
        key_line="Three strategic pillars can drive 30% faster adoption.",
        hypotheses=[
            Hypothesis(
                id=1,
                text="Hybrid cloud solutions drive faster enterprise adoption",
                testable_claim="Enterprises with hybrid strategies grow cloud spending 2x faster",
            ),
            Hypothesis(
                id=2,
                text="Security certifications reduce procurement cycle time",
                testable_claim="SOC2/ISO certified providers close deals 40% faster",
            ),
            Hypothesis(
                id=3,
                text="Flexible pricing improves conversion from trial to paid",
                testable_claim="Pay-as-you-go models convert 3x better than annual contracts",
            ),
        ],
    )


@pytest.fixture
def sample_research_results() -> ResearchResults:
    """Pre-built ResearchResults for 3 hypotheses."""
    evidence_list = []
    for hyp_id in range(1, 4):
        results = [
            SearchResult(
                source=f"Source {hyp_id}-{j}",
                url=f"https://example.com/{hyp_id}/{j}",
                snippet=f"Evidence for hypothesis {hyp_id}, result {j}.",
                date="2025-01",
                relevance_score=0.9,
            )
            for j in range(5)
        ]
        evidence_list.append(
            HypothesisEvidence(
                hypothesis_id=hyp_id,
                evidence=results,
                supports=True,
                confidence="high",
                conclusion=f"Supported - Found 5 relevant sources",
            )
        )
    return ResearchResults(
        hypotheses_evidence=evidence_list,
        total_sources=15,
    )


# ---------------------------------------------------------------------------
# Database fixtures (in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture
def db_engine():
    """In-memory SQLite engine with Job table created."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """SQLAlchemy session bound to in-memory engine."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(db_engine):
    """httpx.AsyncClient against the FastAPI app with overridden DB dependency."""
    import httpx
    from app.main import app
    from sqlalchemy.orm import sessionmaker

    TestSession = sessionmaker(bind=db_engine)

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db

    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PPTX / quality feedback fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_pptx_path(sample_storyline, sample_research_results):
    """Generate a short deck, yield its path, clean up afterward."""
    import asyncio
    from app.agents.slides import SlideGenerator

    gen = SlideGenerator()

    async def _make():
        return await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )

    path = asyncio.get_event_loop().run_until_complete(_make())
    yield path
    if os.path.isfile(path):
        os.remove(path)


@pytest.fixture
def sample_slide_quality_report_json() -> str:
    """Valid JSON string for SlideQualityReport (as the LLM would return it)."""
    return json.dumps({
        "iteration": 1,
        "information_density_score": 55,
        "chart_quality_score": 40,
        "narrative_flow_score": 65,
        "storyline_suggestions": [
            "Add quantitative benchmarks to each hypothesis",
            "Strengthen the MECE grouping in slide 4",
        ],
        "issues": [
            {
                "slide_index": 4,
                "issue_type": "placeholder_data",
                "description": "Bar chart uses generic 'Factor 1-5' labels",
                "fix_suggestion": "Replace with specific market drivers from research",
            },
            {
                "slide_index": 1,
                "issue_type": "missing_so_what",
                "description": "Executive summary lacks a clear recommendation",
                "fix_suggestion": "Add the governing thought as the headline finding",
            },
        ],
    })


@pytest.fixture
def sample_slide_feedback_json() -> str:
    """Valid JSON string for a list of SlideFeedback (as the LLM would return it)."""
    return json.dumps([
        {
            "slide_index": 4,
            "new_title": "Hybrid Cloud Adoption Grows 2x Faster Than On-Prem",
            "new_bullets": [
                "SOC2 certification reduces procurement cycle by 40%",
                "Pay-as-you-go models convert 3x better than annual contracts",
            ],
            "new_chart_data": {
                "chart_type": "bar",
                "categories": ["Hybrid Cloud", "Public Cloud", "On-Premises", "Private Cloud"],
                "values": [85, 75, 45, 60],
                "title": "Enterprise Adoption Rate by Deployment Model (%)",
                "x_label": "Adoption Score",
            },
            "issues_addressed": ["placeholder_data"],
        }
    ])
