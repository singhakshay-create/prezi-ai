# Prezi AI — Implementation Decisions

## Decisions Log

| Decision | Status | Notes |
|----------|--------|-------|
| Research sources | ✅ **Web search only** | Perplexity API + Brave Search + SerpAPI — no proprietary DBs |
| Slide library | ✅ **python-pptx** | Apache 2.0 license, well-documented |
| Deck length | ✅ **Flexible, user-selected** | Short (1-5), Medium (6-15), Long (16+) |
| Pricing | ✅ **Free for MVP** | Revisit monetization after user feedback |
| Framework learning | ✅ **Learn from famous decks** | Ingest consulting frameworks for structure training |
| Collaboration | ✅ **Single user v1** | Team features in Phase 3 |

---

## Deck Configuration (Length Options)

**User selects at input:**

| Option | Slides | Hypotheses | Data Points | Best For |
|--------|--------|------------|-------------|----------|
| **Short** | 1-5 | 2-3 | 1-2 each | Executive update, elevator pitch |
| **Medium** | 6-15 | 3-5 | 3-4 each | Standard business case |
| **Long** | 16+ | 5-8 | 5+ each | Due diligence, deep analysis |

**Structure by length:**
- Short: Executive Summary → Recommendation → 1-2 supporting
- Medium: Situation → Complication → Hypotheses → Analysis → Rec
- Long: Full storyboard + appendices

---

## Framework Library (Training Data)

| Framework | Use |
|-----------|-----|
| McKinsey 7S | Organizational assessment |
| BCG Matrix | Portfolio strategy |
| Hypothesis Pyramid | Argument structuring |
| Issue Tree | Problem breakdown |
| Waterfall Analysis | Financial bridging |
| Porter's 5 Forces | Market assessment |
| Value Chain Analysis | Operations |

*Note: Public frameworks for structure training, not content copying.*
