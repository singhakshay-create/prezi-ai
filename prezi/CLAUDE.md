# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Prezi AI** is an AI-powered tool that generates professional-grade management consulting presentations using Pyramid Principle, MECE structure, and deep research validation. The goal is to transform a raw business topic into a consulting-quality presentation in minutes.

Core workflow: User inputs business topic → AI generates SCQA-structured storyline → Hypothesis-driven research → Generates data-heavy slides → Quality validation → Export to PPTX/PDF.

## Project Status

This repository is currently in the planning phase. The following documents define the project scope:

- `PROJECT_PLAN.md` - Complete feature set, architecture, and implementation phases
- `MVP_SCOPE.md` - Phase 1 MVP definition with sprint breakdown (4-6 weeks)
- `DECISIONS.md` - Key implementation decisions and configuration options

**No code has been written yet.** Implementation will begin when the user is ready.

## Planned Architecture

### Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS (web interface with drag/drop, real-time preview)
- **Backend**: FastAPI + Celery + Redis (async job queue, WebSocket progress updates)
- **AI Engine**: GPT-4/Claude for storyline generation, Perplexity API/Brave Search for research
- **Slide Generation**: python-pptx for PPTX creation, matplotlib for charts
- **Database**: SQLite for MVP, migrate to PostgreSQL for production

### Core Components

1. **Storyline Generator**: SCQA framework (Situation → Complication → Question → Answer) with MECE validation
2. **Research Engine**: Hypothesis-driven research with multi-source validation (web search APIs)
3. **Slide Generator**: Data-heavy consulting slides with chart types (bar, waterfall, Marimekko, tornado, etc.)
4. **Quality Checker Agent**: Reviews slide logic, MECE validation, data quality, and visual consistency
5. **Template System**: Default "McKinsey Classic" template with user template upload support

## MVP Scope (Phase 1)

### Features Included
- Web UI: Topic input with deck length selector (Short/Medium/Long)
- Basic storyline generation (SCQA + 2-5 hypotheses)
- Standard research depth (10-15 sources)
- 3-12 slides depending on length
- 2 chart types: Bar and Waterfall
- PPTX export with McKinsey default template
- Basic quality checker (0-100 score)

### Explicitly Excluded from MVP
- User template upload (Phase 2)
- PDF export (Phase 2)
- Slide editing UI (Phase 2)
- Team collaboration (Phase 3)
- CSV/Excel data upload (Phase 3)
- Advanced chart types beyond bar/waterfall (Phase 2)
- Deep research mode with 20+ sources (Phase 2)
- API access (Phase 3)

## Deck Configuration

Users select deck length at input:

| Option | Slides | Hypotheses | Best For |
|--------|--------|------------|----------|
| Short | 1-5 | 2-3 | Executive update, elevator pitch |
| Medium | 6-15 | 3-5 | Standard business case |
| Long | 16+ | 5-8 | Due diligence, deep analysis |

## Research and Data Sources

**Research sources**: Web search only (no proprietary databases)
- Perplexity API + Brave Search + SerpAPI
- Hypothesis testing: Generate testable hypotheses, validate or disprove with evidence
- Confidence levels: Low/Medium/High per hypothesis
- Citations: All sources cited with IEEE-style references

## Consulting Frameworks

The system learns structure from public consulting frameworks (not content copying):
- McKinsey 7S, BCG Matrix, Hypothesis Pyramid
- Issue Tree, Waterfall Analysis, Porter's 5 Forces, Value Chain Analysis

## Quality Standards

The Quality Checker validates:
- **Slide Logic**: Clear SCQA, logical flow (Critical)
- **MECE Validation**: Mutually exclusive, collectively exhaustive groupings (Critical)
- **So What**: Clear insight present (Critical)
- **Data Quality**: Sources cited, current data (High)
- **Chart Accuracy**: Axes labeled, scales correct (High)
- **Visual Consistency**: Font sizes, colors, alignment (Medium)

Pass threshold: 70/100

## Implementation Philosophy

- **Research-backed**: Every claim must have citations
- **Consulting rigor**: Apply Pyramid Principle and MECE structure
- **Dense, data-heavy slides**: Not minimalist, information-rich like real consulting decks
- **Professional quality**: Slides should be presentation-ready without editing
