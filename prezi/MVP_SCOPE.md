# Prezi AI — MVP Scope Definition
**Phase 1: End-to-End Demo** | Target: 4-6 weeks | Sprint: 1-2 days

---

## 🎯 MVP Success Criteria

A user can:
1. Open web app
2. Enter business topic + select deck length (Short/Medium/Long)
3. Get auto-generated storyline (SCQA + MECE)
4. See research-backed slides with citations
5. Review quality scorecard
6. Download PPTX (McKinsey-style default)

---

## 📋 MVP Feature Breakdown

### F1: Core Web Interface
**Priority:** P0 | **Owner:** Frontend | **Est:** 3 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F1.1 | Landing page with hero + CTA | Page renders, mobile responsive |
| F1.2 | Topic input form | Textarea, deck length selector (radio), submit button |
| F1.3 | Loading state with progress | Shows "Researching...", "Building storyline...", "Generating slides..." |
| F1.4 | Results preview page | Shows slide thumbnails, storyline summary |
| F1.5 | Export button (PPTX) | Click triggers download, spinner while processing |

**Tech:** React + Tailwind + Axios

---

### F2: Backend API
**Priority:** P0 | **Owner:** Backend | **Est:** 2 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F2.1 | FastAPI setup | Server runs, `/health` endpoint responds |
| F2.2 | POST `/generate` endpoint | Accepts `{topic, length}`, returns job_id |
| F2.3 | GET `/status/{job_id}` endpoint | Returns progress: researching → storyline → slides → done |
| F2.4 | GET `/download/{job_id}` endpoint | Returns PPTX file stream |
| F2.5 | Job queue (Celery + Redis) | Jobs process async, no blocking |

**Tech:** FastAPI + Celery + Redis + SQLite (MVP DB)

---

### F3: Storyline Generator
**Priority:** P0 | **Owner:** AI/Backend | **Est:** 2 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F3.1 | SCQA prompt engineering | Input: topic + length → Output: SCQA structure JSON |
| F3.2 | Hypothesis generator | Generates 2-5 testable hypotheses based on topic |
| F3.3 | MECE validation (basic) | Check: Are categories mutually exclusive? (LLM-based) |
| F3.4 | Governing thought extractor | Single unifying message at top of storyline |
| F3.5 | Key line builder | Supporting arguments with logical branches |

**Output Format:**
```json
{
  "scqa": {
    "situation": "...",
    "complication": "...", 
    "question": "...",
    "answer": "..."
  },
  "governing_thought": "...",
  "key_line": ["...", "...", "..."],
  "hypotheses": [
    {"id": 1, "statement": "...", "validated": null}
  ]
}
```

---

### F4: Research Engine
**Priority:** P0 | **Owner:** Backend | **Est:** 3 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F4.1 | Web search integration | Perplexity API or Brave Search working |
| F4.2 | Query expansion | Convert hypotheses → search queries (3 per hypothesis) |
| F4.3 | Source aggregation | Collect: title, URL, snippet, date |
| F4.4 | Evidence extraction | Per source, extract: supports/refutes which hypothesis |
| F4.4 | Confidence scoring | Low/Medium/High per hypothesis based on source quality |
| F4.5 | Citation formatting | IEEE style: [1], [2], etc. with full refs at end |

**Research Depth (MVP):** Standard (10-15 sources)

**Output Format:**
```json
{
  "hypothesis_id": 1,
  "evidence": [
    {"source": "...", "url": "...", "supports": true, "quote": "..."}
  ],
  "confidence": "medium",
  "conclusion": "hypothesis supported with reservations"
}
```

---

### F5: Slide Generator (python-pptx)
**Priority:** P0 | **Owner:** Backend | **Est:** 4 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F5.1 | McKinsey default template | Create .pptx with: header, content area, footer with source |
| F5.2 | Executive Summary slide | Title + 3 bullets max, big font |
| F5.3 | Situation slide | SCQA text + 1 supporting chart |
| F5.4 | Hypothesis Matrix slide | Table: Hypothesis | Evidence | Confidence |
| F5.5 | Recommendation slide | Clear action items + owners |
| F5.6 | Bar chart generation | Matplotlib → embed in slide |
| F5.7 | Waterfall chart generation | Build via python-pptx shapes |
| F5.8 | Source citations slide | Numbered list of all URLs |

**Chart Types (MVP):** Bar, Waterfall only

**Slide Count by Length:**
- Short: 3-4 slides (Summary, Situation, Rec, Sources)
- Medium: 6-8 slides (add Hypothesis Matrix, Evidence slides)
- Long: 10-12 slides (add deep dive slides)

---

### F6: Quality Checker (Basic)
**Priority:** P1 | **Owner:** AI/Backend | **Est:** 2 days

| Task | Description | Done Criteria |
|------|-------------|---------------|
| F6.1 | Structure validator | Checks: SCQA present? Governing thought clear? | Score: 0-25 |
| F6.2 | Evidence validator | Checks: >3 sources? Citations present? | Score: 0-25 |
| F6.3 | Clarity validator | Checks: Jargon? Long sentences? | Score: 0-25 |
| F6.4 | Visual validator | Checks: Font sizes consistent? Charts labeled? | Score: 0-25 |
| F6.5 | Scorecard generator | Total score 0-100, pass/fail per check |
| F6.6 | Improvement suggestions | 3-5 specific fixes suggested |

**Pass Threshold:** 70/100

---

## 🏗️ Technical Architecture (MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│  React + Tailwind                                          │
│  - Simple form → API call → polling → download             │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                      BACKEND                                 │
│  FastAPI + Celery + Redis                                  │
│  - /generate (queue job)                                   │
│  - /status/{id} (poll progress)                            │
│  - /download/{id} (return PPTX)                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    JOB PROCESSOR                           │
│  Celery Worker                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Research   │→│  Storyline  │→│   Slides    │        │
│  │   Agent     │  │   Agent     │  │   Agent     │        │
│  └─────────────┘  └─────────────┘  └──────┬────┘        │
│                                             │              │
│  ┌─────────────┐  ┌─────────────────────────┘             │
│  │   Quality   │←─┘                                       │
│  │   Checker   │                                          │
│  └──────┬──────┘                                          │
└─────────┼───────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────┐
│                   OUTPUT                                   │
│  PPTX file (McKinsey template)                           │
└───────────────────────────────────────────────────────────┘
```

---

## 📅 MVP Sprint Breakdown

### Week 1: Infrastructure
| Day | Task | Owner |
|-----|------|-------|
| 1 | FastAPI + Celery setup | Backend |
| 2 | React app skeleton + Tailwind | Frontend |
| 3 | Redis queue + job status | Backend |
| 4 | Basic form + API integration | Frontend |
| 5 | First end-to-end (mock data) | Both |

**Deliverable:** Click form → see "Processing" → get mock PPTX

### Week 2: AI Pipeline
| Day | Task | Owner |
|-----|------|-------|
| 6 | SCQA prompt + test | AI |
| 7 | Hypothesis generator | AI |
| 8 | Perplexity API integration | Backend |
| 9 | Research → Evidence mapping | Backend |
| 10 | First real storyline working | AI |

### Week 3: Slides + Quality
| Day | Task | Owner |
|-----|------|-------|
| 11 | McKinsey template design | Frontend |
| 12 | python-pptx integration | Backend |
| 13 | Bar chart generation | Backend |
| 14 | Waterfall chart generation | Backend |
| 15 | Slide assembly pipeline | Backend |

### Week 4: Quality + Polish
| Day | Task | Owner |
|-----|------|-------|
| 16 | Quality checker v1 | AI |
| 17 | Scorecard display | Frontend |
| 18 | Error handling + retries | Backend |
| 19 | Testing + bug fixes | Both |
| 20 | Demo prep | Both |

---

## ✅ MVP Definition of Done

- [ ] User can input topic + select length (Short/Medium/Long)
- [ ] System generates SCQA structure automatically
- [ ] 2-5 hypotheses generated, validated with web sources
- [ ] 3-12 slides generated (depending on length selected)
- [ ] PPTX export works, opens in PowerPoint
- [ ] Quality score displayed (0-100)
- [ ] Demo video/screenshots ready
- [ ] Can present to stakeholders

---

## 🚫 MVP Exclusions (Phase 2+)

- User template upload
- PDF export
- Slide editing UI
- Team collaboration
- Team workspaces
- CSV/Excel data upload
- Industry-specific templates
- Advanced chart types (Marimekko, tornado, Sankey)
- Deep research mode (20+ sources)
- API access

---

## 🎯 Next Step

**Choose your priority:**
1. **Start Week 1** — Want me to scaffold the FastAPI + React project? (I can generate the code)
2. **Refine scope** — Add/remove features before we cut code?
3. **Define Phase 2** — Or leave MVP as-is and plan Phase 2?

Or if tomorrow's job applications are priority, we park this here.