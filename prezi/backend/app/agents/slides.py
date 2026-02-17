from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from app.models import Storyline, ResearchResults
from typing import Literal
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime


class SlideGenerator:
    """Generates consulting-style presentations using python-pptx."""

    def __init__(self):
        self.template_path = "app/templates/mckinsey.pptx"
        # McKinsey colors
        self.primary_color = RGBColor(0, 51, 153)  # McKinsey blue
        self.accent_color = RGBColor(0, 176, 240)  # Light blue

    async def create_presentation(
        self,
        topic: str,
        storyline: Storyline,
        research: ResearchResults,
        length: Literal["short", "medium", "long"]
    ) -> str:
        """Create PPTX presentation."""

        # Create presentation
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Add slides based on length
        self._add_title_slide(prs, topic, storyline)
        self._add_executive_summary(prs, storyline)
        self._add_situation_slide(prs, storyline)
        self._add_hypothesis_matrix(prs, storyline, research)

        # Add data slides with charts
        if length in ["medium", "long"]:
            self._add_bar_chart_slide(prs, storyline, research)
            self._add_waterfall_slide(prs, storyline)

        if length == "long":
            self._add_additional_analysis_slides(prs, storyline, research)

        self._add_recommendations(prs, storyline)
        self._add_sources(prs, research)

        # Save presentation
        os.makedirs("./data/presentations", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"presentation_{timestamp}.pptx"
        filepath = f"./data/presentations/{filename}"

        prs.save(filepath)
        return filepath

    def _add_title_slide(self, prs, topic: str, storyline: Storyline):
        """Add title slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

        # Title
        title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = topic
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = self.primary_color
        title_para.alignment = PP_ALIGN.CENTER

        # Subtitle
        subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(1))
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = storyline.governing_thought
        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_para.font.size = Pt(18)
        subtitle_para.alignment = PP_ALIGN.CENTER

        # Date
        date_box = slide.shapes.add_textbox(Inches(1), Inches(6.5), Inches(8), Inches(0.5))
        date_frame = date_box.text_frame
        date_frame.text = datetime.now().strftime("%B %Y")
        date_para = date_frame.paragraphs[0]
        date_para.font.size = Pt(12)
        date_para.alignment = PP_ALIGN.CENTER

    def _add_executive_summary(self, prs, storyline: Storyline):
        """Add executive summary slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Title
        self._add_slide_title(slide, "Executive Summary")

        # Content
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
        tf = content_box.text_frame
        tf.word_wrap = True

        # Add SCQA elements as bullets
        points = [
            f"Situation: {storyline.scqa.situation[:150]}...",
            f"Challenge: {storyline.scqa.complication[:150]}...",
            f"Recommendation: {storyline.scqa.answer[:150]}..."
        ]

        for point in points:
            p = tf.add_paragraph()
            p.text = point
            p.level = 0
            p.font.size = Pt(14)
            p.space_after = Pt(12)

    def _add_situation_slide(self, prs, storyline: Storyline):
        """Add situation/context slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Situation & Context")

        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
        tf = content_box.text_frame
        tf.word_wrap = True

        # Situation
        p = tf.paragraphs[0]
        p.text = "Current Situation"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = self.primary_color

        p = tf.add_paragraph()
        p.text = storyline.scqa.situation
        p.font.size = Pt(12)
        p.space_after = Pt(20)

        # Complication
        p = tf.add_paragraph()
        p.text = "Key Challenge"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = self.primary_color

        p = tf.add_paragraph()
        p.text = storyline.scqa.complication
        p.font.size = Pt(12)

    def _add_hypothesis_matrix(self, prs, storyline: Storyline, research: ResearchResults):
        """Add hypothesis matrix slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Key Hypotheses")

        # Create table
        rows = len(storyline.hypotheses) + 1
        cols = 3
        left = Inches(1)
        top = Inches(1.5)
        width = Inches(8)
        height = Inches(5)

        table = slide.shapes.add_table(rows, cols, left, top, width, height).table

        # Header row
        table.cell(0, 0).text = "Hypothesis"
        table.cell(0, 1).text = "Evidence"
        table.cell(0, 2).text = "Confidence"

        # Data rows
        for i, hyp in enumerate(storyline.hypotheses):
            evidence = next((e for e in research.hypotheses_evidence if e.hypothesis_id == hyp.id), None)

            table.cell(i+1, 0).text = hyp.text[:100]
            table.cell(i+1, 1).text = evidence.conclusion if evidence else "Pending"
            table.cell(i+1, 2).text = evidence.confidence.upper() if evidence else "N/A"

        # Style table
        for row in table.rows:
            for cell in row.cells:
                cell.text_frame.paragraphs[0].font.size = Pt(10)

    def _add_bar_chart_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add slide with bar chart."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Market Analysis")

        # Generate mock bar chart
        fig, ax = plt.subplots(figsize=(8, 4))
        categories = [f"Factor {i+1}" for i in range(5)]
        values = [75, 85, 65, 90, 70]

        ax.barh(categories, values, color='#003399')
        ax.set_xlabel('Impact Score', fontsize=12)
        ax.set_title('Key Success Factors', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        # Save to bytes
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        # Add to slide
        slide.shapes.add_picture(img_bytes, Inches(1.5), Inches(2), width=Inches(7))

    def _add_waterfall_slide(self, prs, storyline: Storyline):
        """Add waterfall chart slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Value Creation Waterfall")

        # Generate waterfall chart
        fig, ax = plt.subplots(figsize=(8, 4))

        categories = ['Starting', 'Revenue\nGrowth', 'Cost\nReduction', 'Efficiency', 'Ending']
        values = [100, 25, 15, 10, 150]
        cumulative = [100, 125, 140, 150, 150]

        colors = ['#0033cc', '#00b0f0', '#00b0f0', '#00b0f0', '#0033cc']

        for i, (cat, val, cum) in enumerate(zip(categories, values, cumulative)):
            if i == 0:
                ax.bar(i, val, color=colors[i], edgecolor='black', linewidth=1)
            elif i == len(categories) - 1:
                ax.bar(i, val, color=colors[i], edgecolor='black', linewidth=1)
            else:
                ax.bar(i, val, bottom=cumulative[i-1], color=colors[i], edgecolor='black', linewidth=1)

        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories)
        ax.set_ylabel('Value ($M)', fontsize=12)
        ax.set_title('Value Creation Opportunity', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.5), Inches(2), width=Inches(7))

    def _add_additional_analysis_slides(self, prs, storyline: Storyline, research: ResearchResults):
        """Add extra analysis slides for long decks."""
        for i in range(2):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            self._add_slide_title(slide, f"Deep Dive Analysis {i+1}")

            content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
            tf = content_box.text_frame
            tf.word_wrap = True

            p = tf.paragraphs[0]
            p.text = f"Additional analysis supporting hypothesis {i+1}"
            p.font.size = Pt(14)

    def _add_recommendations(self, prs, storyline: Storyline):
        """Add recommendations slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Recommendations")

        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
        tf = content_box.text_frame
        tf.word_wrap = True

        # Answer from SCQA
        p = tf.paragraphs[0]
        p.text = "Recommended Actions"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = self.primary_color

        p = tf.add_paragraph()
        p.text = storyline.scqa.answer
        p.font.size = Pt(12)
        p.space_after = Pt(20)

        # Next steps
        p = tf.add_paragraph()
        p.text = "Next Steps"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = self.primary_color

        for i in range(3):
            p = tf.add_paragraph()
            p.text = f"Action item {i+1}: Implement key recommendations"
            p.level = 0
            p.font.size = Pt(12)

    def _add_sources(self, prs, research: ResearchResults):
        """Add sources/references slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Sources")

        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
        tf = content_box.text_frame
        tf.word_wrap = True

        # Collect unique sources
        sources_seen = set()
        source_num = 1

        for hyp_evidence in research.hypotheses_evidence:
            for evidence in hyp_evidence.evidence[:3]:  # Top 3 per hypothesis
                if evidence.url not in sources_seen:
                    sources_seen.add(evidence.url)
                    p = tf.add_paragraph() if source_num > 1 else tf.paragraphs[0]
                    p.text = f"[{source_num}] {evidence.source} - {evidence.url}"
                    p.font.size = Pt(8)
                    p.space_after = Pt(6)
                    source_num += 1

                    if source_num > 15:  # Limit sources
                        break

    def _add_slide_title(self, slide, title: str):
        """Add title to slide."""
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(0.75))
        title_frame = title_box.text_frame
        title_frame.text = title
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(24)
        title_para.font.bold = True
        title_para.font.color.rgb = self.primary_color
