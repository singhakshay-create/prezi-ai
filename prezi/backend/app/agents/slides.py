from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn
from app.models import Storyline, ResearchResults
from typing import Literal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
import os
from datetime import datetime


class SlideGenerator:
    """Generates consulting-style presentations using python-pptx."""

    def __init__(self, template_path: str = None):
        self.template_path = template_path
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

        # Create presentation (use template if provided)
        if self.template_path and os.path.isfile(self.template_path):
            prs = Presentation(self.template_path)
        else:
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
            self._add_pie_chart_slide(prs, storyline, research)
            self._add_tornado_chart_slide(prs, storyline, research)

        if length == "long":
            self._add_marimekko_chart_slide(prs, storyline, research)
            self._add_bcg_matrix_slide(prs, storyline, research)
            self._add_priority_matrix_slide(prs, storyline)
            self._add_value_chain_slide(prs, storyline)
            self._add_heatmap_slide(prs, storyline, research)

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

    def _add_pie_chart_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add pie chart slide for market segmentation."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Market Segmentation")

        fig, ax = plt.subplots(figsize=(8, 4))
        segments = ['Segment A', 'Segment B', 'Segment C', 'Segment D', 'Segment E']
        sizes = [30, 25, 20, 15, 10]
        colors = ['#003399', '#00b0f0', '#0066cc', '#66b3ff', '#99ccff']

        wedges, texts, autotexts = ax.pie(
            sizes, labels=segments, colors=colors,
            autopct='%1.0f%%', startangle=90, textprops={'fontsize': 10}
        )
        for t in autotexts:
            t.set_fontsize(10)
            t.set_fontweight('bold')
        ax.set_title('Market Share by Segment', fontsize=14, fontweight='bold')

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.5), Inches(2), width=Inches(7))

    def _add_tornado_chart_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add tornado chart slide for sensitivity analysis."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Sensitivity Analysis")

        fig, ax = plt.subplots(figsize=(8, 4))
        factors = ['Market Size', 'Pricing', 'Cost Structure', 'Growth Rate', 'Competition']
        upside = [30, 20, 15, 25, 10]
        downside = [-25, -15, -20, -10, -18]

        y_pos = range(len(factors))
        ax.barh(y_pos, upside, color='#003399', edgecolor='black', linewidth=0.5, label='Upside')
        ax.barh(y_pos, downside, color='#00b0f0', edgecolor='black', linewidth=0.5, label='Downside')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(factors)
        ax.axvline(x=0, color='black', linewidth=1)
        ax.set_xlabel('Impact (%)', fontsize=12)
        ax.set_title('Key Sensitivities', fontsize=14, fontweight='bold')
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(axis='x', alpha=0.3)

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.5), Inches(2), width=Inches(7))

    def _add_marimekko_chart_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add Marimekko (variable-width stacked bar) chart slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Market Structure")

        fig, ax = plt.subplots(figsize=(8, 4))

        # Segment data: name, width (market size), sub-segment shares
        segments = [
            ('Enterprise', 40, [0.6, 0.25, 0.15]),
            ('Mid-Market', 30, [0.4, 0.35, 0.25]),
            ('SMB', 20, [0.3, 0.3, 0.4]),
            ('Consumer', 10, [0.5, 0.3, 0.2]),
        ]
        sub_labels = ['Premium', 'Standard', 'Economy']
        sub_colors = ['#003399', '#00b0f0', '#99ccff']

        x_offset = 0
        for seg_name, width, shares in segments:
            bottom = 0
            for j, (share, color) in enumerate(zip(shares, sub_colors)):
                height = share * 100
                ax.bar(x_offset + width / 2, height, width=width, bottom=bottom,
                       color=color, edgecolor='white', linewidth=1,
                       label=sub_labels[j] if x_offset == 0 else None)
                bottom += height
            ax.text(x_offset + width / 2, -5, seg_name, ha='center', fontsize=9)
            x_offset += width

        ax.set_xlim(0, 100)
        ax.set_ylim(-10, 110)
        ax.set_ylabel('Share (%)', fontsize=12)
        ax.set_title('Market Structure Analysis', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.set_xticks([])

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.5), Inches(2), width=Inches(7))

    def _add_bcg_matrix_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add BCG Growth-Share Matrix slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Portfolio Analysis — BCG Growth-Share Matrix")

        fig, ax = plt.subplots(figsize=(7, 4.5))

        # Quadrant backgrounds
        ax.axhline(y=10, color='#cccccc', linewidth=1.5, linestyle='--')
        ax.axvline(x=1.0, color='#cccccc', linewidth=1.5, linestyle='--')
        ax.set_facecolor('#f9f9f9')

        quadrant_colors = ['#e8f4fc', '#e8f4fc', '#fef9e7', '#fef9e7']
        for (x0, x1, y0, y1), c in zip(
            [(1.0, 4.0, 10, 30), (0.0, 1.0, 10, 30),
             (1.0, 4.0, 0, 10), (0.0, 1.0, 0, 10)],
            quadrant_colors
        ):
            ax.fill_between([x0, x1], y0, y1, color=c, alpha=0.5)

        # Quadrant labels
        ax.text(2.5, 27, 'STARS', ha='center', fontsize=10, fontweight='bold', color='#003399')
        ax.text(0.5, 27, 'QUESTION\nMARKS', ha='center', fontsize=9, color='#666666')
        ax.text(2.5, 2,  'CASH COWS', ha='center', fontsize=10, fontweight='bold', color='#003399')
        ax.text(0.5, 2,  'DOGS', ha='center', fontsize=9, color='#888888')

        # Business units (bubble size = revenue)
        units = [
            ('BU-A', 2.4, 22, 1200, '#003399'),
            ('BU-B', 0.6, 18, 500,  '#00b0f0'),
            ('BU-C', 2.8, 5,  2500, '#003399'),
            ('BU-D', 0.4, 3,  400,  '#bbbbbb'),
            ('BU-E', 1.5, 14, 800,  '#0066cc'),
        ]
        for name, x, y, size, color in units:
            ax.scatter(x, y, s=size / 5, color=color, alpha=0.85, edgecolors='white', linewidth=1.5, zorder=5)
            ax.annotate(name, (x, y), textcoords='offset points', xytext=(5, 5),
                        fontsize=9, fontweight='bold', color='#111111')

        ax.set_xlim(0, 4)
        ax.set_ylim(0, 30)
        ax.set_xlabel('Relative Market Share  →  High', fontsize=10)
        ax.set_ylabel('Market Growth Rate (%)  →  High', fontsize=10)
        ax.invert_xaxis()
        ax.grid(False)

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.2), Inches(1.8), width=Inches(7.5))

    def _add_priority_matrix_slide(self, prs, storyline: Storyline):
        """Add 2×2 Impact vs. Effort priority matrix slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Prioritization — Impact vs. Effort Matrix")

        fig, ax = plt.subplots(figsize=(7, 4.5))

        # Quadrant fills
        fills = [
            (0, 5, 5, 10, '#e3f2fd', 'Quick Wins\n(Do First)'),
            (5, 10, 5, 10, '#fff8e1', 'Strategic\nProjects'),
            (0, 5, 0, 5,  '#f3e5f5', 'Fill-ins\n(Low priority)'),
            (5, 10, 0, 5,  '#fce4ec', 'Avoid /\nDelegate'),
        ]
        for x0, x1, y0, y1, color, label in fills:
            ax.fill_between([x0, x1], y0, y1, color=color, alpha=0.8)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(cx, cy + 1.5, label, ha='center', va='center', fontsize=9,
                    fontweight='bold', color='#444444',
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.6, ec='none'))

        ax.axhline(y=5, color='#888888', linewidth=1.5, linestyle='--')
        ax.axvline(x=5, color='#888888', linewidth=1.5, linestyle='--')

        # Initiatives
        initiatives = [
            ('Digital Platform', 3, 8.5, 180),
            ('Cost Automation', 2, 7, 120),
            ('M&A Integration', 8, 8, 200),
            ('Analytics BI', 7, 6, 140),
            ('Process Redesign', 3, 3, 90),
            ('Vendor Review', 2, 2, 60),
            ('CRM Upgrade', 8, 2, 80),
        ]
        colors_map = {
            'Digital Platform': '#003399', 'Cost Automation': '#003399',
            'M&A Integration': '#0066cc', 'Analytics BI': '#0066cc',
            'Process Redesign': '#9c27b0', 'Vendor Review': '#9c27b0',
            'CRM Upgrade': '#e53935',
        }
        for name, effort, impact, size in initiatives:
            c = colors_map.get(name, '#003399')
            ax.scatter(effort, impact, s=size, color=c, alpha=0.85,
                       edgecolors='white', linewidth=1.5, zorder=5)
            ax.annotate(name, (effort, impact), textcoords='offset points',
                        xytext=(6, 4), fontsize=8, color='#111111')

        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.set_xlabel('Effort / Complexity  →', fontsize=10)
        ax.set_ylabel('Business Impact  →', fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.2, 9.5, 'Low Effort', fontsize=8, color='#555555')
        ax.text(8.5, 9.5, 'High Effort', fontsize=8, color='#555555')
        ax.text(0.2, 0.3, 'Low Impact', fontsize=8, color='#555555')
        ax.text(0.2, 9.0, 'High Impact', fontsize=8, color='#555555')

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(1.2), Inches(1.8), width=Inches(7.5))

    def _add_value_chain_slide(self, prs, storyline: Storyline):
        """Add Porter Value Chain slide using native PPTX shapes (no image embed)."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Value Chain Analysis")

        # ── Primary activities ───────────────────────────────────────────────
        primary = [
            ('Inbound\nLogistics', '#003399'),
            ('Operations', '#0044cc'),
            ('Outbound\nLogistics', '#0055dd'),
            ('Marketing\n& Sales', '#0066ee'),
            ('Service', '#0077ff'),
        ]
        box_w, box_h = Inches(1.5), Inches(1.0)
        top_y = Inches(2.0)
        start_x = Inches(0.5)
        gap = Inches(0.12)

        for i, (label, color) in enumerate(primary):
            x = start_x + i * (box_w + gap)
            shape = slide.shapes.add_shape(
                1,  # MSO_SHAPE_TYPE.RECTANGLE
                x, top_y, box_w, box_h
            )
            shape.fill.solid()
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            shape.fill.fore_color.rgb = RGBColor(r, g, b)
            shape.line.color.rgb = RGBColor(255, 255, 255)
            tf = shape.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = label
            p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(9)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)

        # Margin box on right
        margin_x = start_x + 5 * (box_w + gap)
        margin_shape = slide.shapes.add_shape(
            1, margin_x, top_y, Inches(1.1), box_h
        )
        margin_shape.fill.solid()
        margin_shape.fill.fore_color.rgb = RGBColor(0, 51, 153)
        margin_shape.line.color.rgb = RGBColor(255, 255, 255)
        tf = margin_shape.text_frame
        p = tf.paragraphs[0]
        p.text = 'Margin'
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

        # ── Support activities ───────────────────────────────────────────────
        support = [
            ('Firm Infrastructure', '#4a6fa5'),
            ('Human Resource Management', '#5d7db5'),
            ('Technology Development', '#7090c4'),
            ('Procurement', '#839fd3'),
        ]
        sup_h = Inches(0.55)
        sup_w = Inches(8.1)  # full width
        sup_x = start_x
        for i, (label, color) in enumerate(support):
            y = top_y + box_h + Inches(0.12) + i * (sup_h + Inches(0.06))
            s = slide.shapes.add_shape(1, sup_x, y, sup_w, sup_h)
            s.fill.solid()
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            s.fill.fore_color.rgb = RGBColor(r, g, b)
            s.line.color.rgb = RGBColor(255, 255, 255)
            tf = s.text_frame
            p = tf.paragraphs[0]
            p.text = label
            p.alignment = PP_ALIGN.LEFT
            p.font.size = Pt(9)
            p.font.color.rgb = RGBColor(255, 255, 255)

        # Label
        lbl = slide.shapes.add_textbox(start_x, Inches(1.72), Inches(4), Inches(0.25))
        lp = lbl.text_frame.paragraphs[0]
        lp.text = 'Primary Activities'
        lp.font.size = Pt(9)
        lp.font.bold = True
        lp.font.color.rgb = RGBColor(0, 51, 153)

        lbl2 = slide.shapes.add_textbox(start_x, top_y + box_h + Inches(0.05), Inches(2), Inches(0.22))
        lp2 = lbl2.text_frame.paragraphs[0]
        lp2.text = 'Support Activities'
        lp2.font.size = Pt(9)
        lp2.font.bold = True
        lp2.font.color.rgb = RGBColor(0, 51, 153)

    def _add_heatmap_slide(self, prs, storyline: Storyline, research: ResearchResults):
        """Add competitive landscape heatmap slide."""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self._add_slide_title(slide, "Competitive Landscape — Capability Heatmap")

        fig, ax = plt.subplots(figsize=(8, 4))

        capabilities = ['Digital', 'Operations', 'Talent', 'Innovation', 'Customer\nExp.', 'Cost\nEfficiency']
        competitors = ['Our Co.', 'Competitor A', 'Competitor B', 'Competitor C', 'Competitor D']

        np.random.seed(42)
        data = np.array([
            [9, 7, 8, 8, 9, 7],
            [6, 8, 5, 6, 7, 9],
            [7, 6, 7, 5, 6, 8],
            [5, 7, 6, 7, 5, 6],
            [4, 5, 4, 6, 4, 7],
        ], dtype=float)

        cmap = plt.cm.RdYlGn
        im = ax.imshow(data, cmap=cmap, vmin=1, vmax=10, aspect='auto')

        ax.set_xticks(range(len(capabilities)))
        ax.set_xticklabels(capabilities, fontsize=10)
        ax.set_yticks(range(len(competitors)))
        ax.set_yticklabels(competitors, fontsize=10)

        # Annotate cells
        for i in range(len(competitors)):
            for j in range(len(capabilities)):
                val = data[i, j]
                text_color = 'white' if val < 4 or val > 8 else 'black'
                ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                        fontsize=11, fontweight='bold', color=text_color)

        # Highlight "Our Co." row
        for j in range(len(capabilities)):
            ax.add_patch(plt.Rectangle((j - 0.5, -0.5), 1, 1,
                                        fill=False, edgecolor='#003399', linewidth=2.5))

        plt.colorbar(im, ax=ax, label='Score (1–10)', shrink=0.8)
        ax.set_title('Competitive Capability Assessment', fontsize=13, fontweight='bold', pad=10)

        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()

        slide.shapes.add_picture(img_bytes, Inches(0.8), Inches(1.8), width=Inches(8.4))

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
