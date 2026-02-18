"""Tests for QualityChecker agent."""

import json
import pytest

from app.agents.quality import QualityChecker
from app.models import QualityScore, SlideQualityReport, SlideFeedback
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


class TestQualityCheckerWithPptx:
    """Tests for the PPTX-aware quality checking methods."""

    def test_extract_pptx_content_returns_slide_list(
        self, sample_pptx_path, sample_storyline
    ):
        """Short deck (6 slides) → list of 6 SlideContent objects."""
        from app.models import SlideContent

        checker = QualityChecker(MockLLMProvider())
        slides = checker._extract_pptx_content(sample_pptx_path)

        assert len(slides) == 6
        for s in slides:
            assert isinstance(s, SlideContent)
            assert s.slide_index >= 0
            assert isinstance(s.word_count, int)

    def test_extract_detects_charts(self, sample_storyline, sample_research_results):
        """Medium deck → slides with chart images have has_chart=True."""
        import asyncio
        import os
        from app.agents.slides import SlideGenerator

        gen = SlideGenerator()
        path = asyncio.get_event_loop().run_until_complete(
            gen.create_presentation("Cloud Strategy", sample_storyline, sample_research_results, "medium")
        )
        try:
            checker = QualityChecker(MockLLMProvider())
            slides = checker._extract_pptx_content(path)
            chart_slides = [s for s in slides if s.has_chart]
            # medium has 4 chart slides (bar, waterfall, pie, tornado)
            assert len(chart_slides) >= 4
        finally:
            if os.path.isfile(path):
                os.remove(path)

    async def test_inspect_fallback_on_bad_llm_json(
        self, sample_pptx_path, sample_storyline
    ):
        """If LLM returns garbage, _inspect_with_llm returns scores of 50 and 0 issues."""
        checker = QualityChecker(MockLLMProvider(response="not valid json at all"))
        slides = checker._extract_pptx_content(sample_pptx_path)
        report = await checker._inspect_with_llm(slides, sample_storyline, 1)

        assert isinstance(report, SlideQualityReport)
        assert report.information_density_score == 50
        assert report.chart_quality_score == 50
        assert report.narrative_flow_score == 50
        assert report.issues == []

    async def test_check_with_pptx_returns_triple(
        self,
        sample_pptx_path,
        sample_storyline,
        sample_research_results,
        sample_slide_quality_report_json,
        sample_slide_feedback_json,
    ):
        """check_with_pptx returns (QualityScore, SlideQualityReport, list)."""
        call_count = 0

        class SequentialMockLLM(MockLLMProvider):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4000):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    self.response = sample_slide_quality_report_json
                else:
                    self.response = sample_slide_feedback_json
                return await super().generate(prompt, system, temperature, max_tokens)

        llm = SequentialMockLLM()
        checker = QualityChecker(llm)

        result = await checker.check_with_pptx(
            sample_pptx_path, sample_storyline, sample_research_results, 1
        )

        assert len(result) == 3
        score, report, feedback = result
        assert isinstance(score, QualityScore)
        assert isinstance(report, SlideQualityReport)
        assert isinstance(feedback, list)


class TestVisualInspection:
    """Tests for the screenshot-based visual quality path."""

    def test_render_slide_screenshots_returns_pngs(self, sample_pptx_path):
        """_render_slide_screenshots returns one PNG per slide for a valid PPTX."""
        checker = QualityChecker(MockLLMProvider())
        png_paths, temp_dir = checker._render_slide_screenshots(sample_pptx_path)
        try:
            assert len(png_paths) == 6
            import os
            for p in png_paths:
                assert os.path.isfile(p)
                assert os.path.getsize(p) > 0
        finally:
            if temp_dir:
                from app.agents.screenshot import cleanup_screenshots
                cleanup_screenshots(temp_dir)

    def test_render_slide_screenshots_returns_empty_on_bad_path(self):
        """_render_slide_screenshots returns ([], None) for a non-existent file."""
        checker = QualityChecker(MockLLMProvider())
        png_paths, temp_dir = checker._render_slide_screenshots("/tmp/no_such_file.pptx")
        assert png_paths == []
        assert temp_dir is None

    async def test_visual_inspect_uses_generate_with_vision(
        self, sample_pptx_path, sample_storyline, sample_research_results,
        sample_slide_quality_report_json,
    ):
        """check_with_pptx routes through generate_with_vision when LLM supports it."""
        vision_calls = []
        llm = MockLLMProvider(response=sample_slide_quality_report_json)

        orig_vision = llm.generate_with_vision
        async def _tracking_vision(prompt, image_paths, **kwargs):
            vision_calls.append(image_paths)
            return await orig_vision(prompt, image_paths, **kwargs)
        llm.generate_with_vision = _tracking_vision

        # Feedback call returns empty list so we don't need extra mocking
        orig_gen = llm.generate
        async def _feedback_fallback(prompt, **kwargs):
            return "[]"
        llm.generate = _feedback_fallback

        checker = QualityChecker(llm)
        await checker.check_with_pptx(
            sample_pptx_path, sample_storyline, sample_research_results, 1
        )
        assert len(vision_calls) >= 1
        # Each vision call received a non-empty list of PNG paths
        assert len(vision_calls[0]) > 0

    async def test_visual_inspect_fallback_on_bad_json(
        self, sample_pptx_path, sample_storyline, sample_research_results
    ):
        """Visual inspection with bad LLM JSON falls back to 50/50/50, no crash."""
        llm = MockLLMProvider(response="not valid json at all {{{")
        checker = QualityChecker(llm)
        score, report, feedback = await checker.check_with_pptx(
            sample_pptx_path, sample_storyline, sample_research_results, 1
        )
        assert isinstance(score, QualityScore)
        assert report.information_density_score == 50
        assert report.issues == []
