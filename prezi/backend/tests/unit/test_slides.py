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
        """Medium deck: short (6) + bar + waterfall + pie + tornado = 10."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "medium"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 10
        finally:
            os.remove(path)

    async def test_long_slide_count(self, sample_storyline, sample_research_results):
        """Long deck: medium (10) + marimekko + BCG + priority + value chain + heatmap = 15."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "long"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 15
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

    async def test_medium_has_chart_images(self, sample_storyline, sample_research_results):
        """Medium deck has 4 chart image shapes (bar, waterfall, pie, tornado)."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "medium"
        )
        try:
            prs = Presentation(path)
            picture_count = sum(
                1 for slide in prs.slides for shape in slide.shapes
                if shape.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE
            )
            assert picture_count == 4
        finally:
            os.remove(path)

    async def test_long_has_framework_slides(self, sample_storyline, sample_research_results):
        """Long deck has 8 chart images: bar, waterfall, pie, tornado, marimekko, BCG, priority, heatmap.
        Value chain uses native PPTX shapes and contributes 0 pictures."""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "long"
        )
        try:
            prs = Presentation(path)
            picture_count = sum(
                1 for slide in prs.slides for shape in slide.shapes
                if shape.shape_type == 13  # MSO_SHAPE_TYPE.PICTURE
            )
            assert picture_count == 8
        finally:
            os.remove(path)

    async def test_value_chain_has_native_shapes(self, sample_storyline, sample_research_results):
        """Value chain slide uses native PPTX rectangles, no embedded images.
        Slide order (long): 0=title 1=exec 2=situation 3=hypotheses 4=bar 5=waterfall
        6=pie 7=tornado 8=marimekko 9=BCG 10=priority 11=value-chain 12=heatmap 13=recs 14=sources"""
        gen = SlideGenerator()
        path = await gen.create_presentation(
            "Cloud Strategy", sample_storyline, sample_research_results, "long"
        )
        try:
            prs = Presentation(path)
            assert len(prs.slides) == 15
            value_chain_slide = prs.slides[11]
            pictures = [s for s in value_chain_slide.shapes if s.shape_type == 13]
            rectangles = [s for s in value_chain_slide.shapes if s.shape_type == 1]
            assert len(pictures) == 0
            assert len(rectangles) >= 9  # 5 primary + 4 support activity boxes
        finally:
            os.remove(path)

    async def test_slides_with_template_path(self, sample_storyline, sample_research_results):
        """SlideGenerator with a template_path produces a valid PPTX."""
        # Create a minimal template
        template_prs = Presentation()
        template_prs.slide_width = Inches(10)
        template_prs.slide_height = Inches(7.5)
        os.makedirs("./data/templates", exist_ok=True)
        template_path = "./data/templates/test_template.pptx"
        template_prs.save(template_path)

        try:
            gen = SlideGenerator(template_path=template_path)
            path = await gen.create_presentation(
                "Cloud Strategy", sample_storyline, sample_research_results, "short"
            )
            try:
                prs = Presentation(path)
                assert prs is not None
                assert len(prs.slides) == 6
            finally:
                os.remove(path)
        finally:
            os.remove(template_path)
