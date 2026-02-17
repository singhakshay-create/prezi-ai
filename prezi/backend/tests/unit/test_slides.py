"""Tests for SlideGenerator agent."""

import os
import pytest
from pptx import Presentation
from pptx.util import Inches

from app.agents.slides import SlideGenerator
from app.models import Storyline, ResearchResults


class TestSlideGenerator:
    """Tests for SlideGenerator.create_presentation()."""

    async def test_short_slide_count(self, sample_storyline, sample_research_results):
        """Short deck: title + exec summary + situation + hypothesis matrix + recommendations + sources = 6."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 6
        finally:
            os.remove(path)

    async def test_medium_slide_count(self, sample_storyline, sample_research_results):
        """Medium deck: short (6) + bar chart + waterfall = 8."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "medium"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 8
        finally:
            os.remove(path)

    async def test_long_slide_count(self, sample_storyline, sample_research_results):
        """Long deck: medium (8) + 2 additional analysis slides = 10."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "long"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 10
        finally:
            os.remove(path)

    async def test_pptx_valid(self, sample_storyline, sample_research_results):
        """Output file opens with Presentation() without error."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            assert prs is not None
        finally:
            os.remove(path)

    async def test_title_contains_topic(self, sample_storyline, sample_research_results):
        """First slide text includes the topic string."""
        gen = SlideGenerator()
        topic = "Cloud Strategy for Fortune 500"
        path = await gen.create_presentation(
            topic, sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            first_slide = prs.slides[0]
            texts = [shape.text_frame.text for shape in first_slide.shapes if shape.has_text_frame]
            combined = " ".join(texts)
            assert topic in combined
        finally:
            os.remove(path)

    async def test_exec_summary_has_scqa(self, sample_storyline, sample_research_results):
        """Second slide contains situation, complication, and answer text."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            second_slide = prs.slides[1]
            texts = [shape.text_frame.text for shape in second_slide.shapes if shape.has_text_frame]
            combined = " ".join(texts)
            # The exec summary truncates to 150 chars, so check prefix
            assert sample_storyline.scqa.situation[:50] in combined
            assert sample_storyline.scqa.complication[:50] in combined
            assert sample_storyline.scqa.answer[:50] in combined
        finally:
            os.remove(path)

    async def test_hypothesis_table_rows(self, sample_storyline, sample_research_results):
        """Hypothesis matrix slide has table with header + N hypothesis rows."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            # Hypothesis matrix is 4th slide (index 3)
            hyp_slide = prs.slides[3]
            tables = [s for s in hyp_slide.shapes if s.has_table]
            assert len(tables) == 1
            table = tables[0].table
            # header + 3 hypothesis rows
            assert len(table.rows) == 1 + len(sample_storyline.hypotheses)
        finally:
            os.remove(path)

    async def test_slide_dimensions(self, sample_storyline, sample_research_results):
        """Slide dimensions are 10" x 7.5"."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            prs = Presentation(path)
            assert prs.slide_width == Inches(10)
            assert prs.slide_height == Inches(7.5)
        finally:
            os.remove(path)

    async def test_output_path_pattern(self, sample_storyline, sample_research_results):
        """File saved to ./data/presentations/presentation_*.pptx."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "short"
        )
        try:
            assert path.startswith("./data/presentations/presentation_")
            assert path.endswith(".pptx")
            assert os.path.isfile(path)
        finally:
            os.remove(path)
