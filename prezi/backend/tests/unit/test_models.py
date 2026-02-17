"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from app.models import (
    GenerateRequest,
    SCQAFramework,
    Hypothesis,
    Storyline,
    SearchResult,
    HypothesisEvidence,
    QualityScore,
    JobStatus,
)


# --- GenerateRequest ---


class TestGenerateRequest:
    def test_valid(self):
        req = GenerateRequest(
            topic="Cloud computing strategy for enterprise adoption",
            length="medium",
            llm_provider="claude",
        )
        assert req.topic == "Cloud computing strategy for enterprise adoption"
        assert req.length == "medium"
        assert req.research_provider == "mock"

    def test_topic_too_short(self):
        with pytest.raises(ValidationError):
            GenerateRequest(topic="Short", length="short", llm_provider="claude")

    def test_topic_too_long(self):
        with pytest.raises(ValidationError):
            GenerateRequest(topic="X" * 501, length="short", llm_provider="claude")

    def test_invalid_length(self):
        with pytest.raises(ValidationError):
            GenerateRequest(
                topic="A valid topic that is long enough",
                length="extra",
                llm_provider="claude",
            )


# --- SCQAFramework ---


class TestSCQAFramework:
    def test_requires_all_fields(self):
        with pytest.raises(ValidationError):
            SCQAFramework(situation="sit", complication="comp", question="q")


# --- Hypothesis ---


class TestHypothesis:
    def test_valid(self):
        h = Hypothesis(id=1, text="Some hypothesis", testable_claim="Claim X")
        assert h.id == 1
        assert h.text == "Some hypothesis"


# --- Storyline ---


class TestStoryline:
    def test_full_storyline(self, sample_storyline):
        assert len(sample_storyline.hypotheses) == 3
        assert sample_storyline.scqa.situation.startswith("The global")


# --- SearchResult ---


class TestSearchResult:
    def test_relevance_too_high(self):
        with pytest.raises(ValidationError):
            SearchResult(
                source="S", url="http://x", snippet="s", relevance_score=1.1
            )

    def test_relevance_too_low(self):
        with pytest.raises(ValidationError):
            SearchResult(
                source="S", url="http://x", snippet="s", relevance_score=-0.1
            )


# --- HypothesisEvidence ---


class TestHypothesisEvidence:
    def test_confidence_literals(self):
        """Only 'low', 'medium', 'high' are accepted."""
        with pytest.raises(ValidationError):
            HypothesisEvidence(
                hypothesis_id=1,
                evidence=[],
                supports=True,
                confidence="very_high",
                conclusion="test",
            )


# --- QualityScore ---


class TestQualityScore:
    def test_bounds(self):
        with pytest.raises(ValidationError):
            QualityScore(
                overall_score=101,
                slide_logic=80,
                mece_structure=80,
                so_what=80,
                data_quality=80,
                chart_accuracy=80,
                visual_consistency=80,
                suggestions=[],
            )

    def test_with_suggestions(self):
        qs = QualityScore(
            overall_score=80,
            slide_logic=80,
            mece_structure=80,
            so_what=80,
            data_quality=80,
            chart_accuracy=80,
            visual_consistency=80,
            suggestions=["Improve charts", "Add more data"],
        )
        assert len(qs.suggestions) == 2


# --- JobStatus ---


class TestJobStatus:
    def test_valid_statuses(self):
        for status in ["queued", "storyline", "researching", "slides", "quality", "completed", "failed"]:
            js = JobStatus(job_id="abc", status=status, progress=50, message="msg")
            assert js.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            JobStatus(job_id="abc", status="unknown", progress=50, message="msg")
