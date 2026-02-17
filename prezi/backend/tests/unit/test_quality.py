"""Tests for QualityChecker agent."""

import json
import pytest

from app.agents.quality import QualityChecker
from app.models import QualityScore
from tests.conftest import MockLLMProvider


class TestQualityChecker:
    async def test_parses_valid_scores(self, sample_quality_json, sample_storyline):
        """Valid JSON → QualityScore with correct dimensions."""
        llm = MockLLMProvider(response=sample_quality_json)
        checker = QualityChecker(llm)
        result = await checker.check(sample_storyline)

        assert isinstance(result, QualityScore)
        assert result.slide_logic == 85
        assert result.mece_structure == 80
        assert result.so_what == 90
        assert result.data_quality == 85
        assert result.chart_accuracy == 80
        assert result.visual_consistency == 85

    async def test_weighted_average(self, sample_quality_json, sample_storyline):
        """overall = logic*0.25 + mece*0.25 + sowhat*0.25 + data*0.15 + chart*0.05 + visual*0.05."""
        llm = MockLLMProvider(response=sample_quality_json)
        checker = QualityChecker(llm)
        result = await checker.check(sample_storyline)

        expected = int(
            85 * 0.25 + 80 * 0.25 + 90 * 0.25 + 85 * 0.15 + 80 * 0.05 + 85 * 0.05
        )
        assert result.overall_score == expected

    async def test_handles_code_block(self, sample_quality_json, sample_storyline):
        """```json ``` wrapping → correct parsing."""
        wrapped = f"```json\n{sample_quality_json}\n```"
        llm = MockLLMProvider(response=wrapped)
        checker = QualityChecker(llm)
        result = await checker.check(sample_storyline)

        assert isinstance(result, QualityScore)
        assert result.slide_logic == 85

    async def test_fallback_on_invalid_json(self, sample_storyline):
        """Garbage → default QualityScore (all 75s)."""
        llm = MockLLMProvider(response="This is not JSON")
        checker = QualityChecker(llm)
        result = await checker.check(sample_storyline)

        assert result.overall_score == 75
        assert result.slide_logic == 75
        assert result.mece_structure == 75

    async def test_fallback_on_missing_key(self, sample_storyline):
        """Missing 'slide_logic' → default scores."""
        bad_json = json.dumps({"mece_structure": 80, "so_what": 90})
        llm = MockLLMProvider(response=bad_json)
        checker = QualityChecker(llm)
        result = await checker.check(sample_storyline)

        assert result.overall_score == 75

    async def test_low_temperature(self, sample_quality_json, sample_storyline):
        """LLM called with temperature=0.3."""
        llm = MockLLMProvider(response=sample_quality_json)
        checker = QualityChecker(llm)
        await checker.check(sample_storyline)

        assert llm.calls[0]["temperature"] == 0.3

    async def test_prompt_contains_storyline(self, sample_quality_json, sample_storyline):
        """Prompt includes SCQA elements and hypotheses."""
        llm = MockLLMProvider(response=sample_quality_json)
        checker = QualityChecker(llm)
        await checker.check(sample_storyline)

        prompt = llm.calls[0]["prompt"]
        assert sample_storyline.scqa.situation in prompt
        assert sample_storyline.scqa.complication in prompt
        assert sample_storyline.hypotheses[0].text in prompt
