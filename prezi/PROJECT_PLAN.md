# Consulting PPT Generator — Project Plan
**Codename:** Prezi AI  
**Objective:** An AI-powered tool that generates professional-grade management consulting presentations using Pyramid Principle, MECE structure, and deep research validation.

---

## 🎯 Core Value Proposition

Transform a raw business topic into a consulting-quality presentation in minutes — not days. Think of it as having a McKinsey/Bain/BCG associate working 24/7.

---

## ✅ Confirmed Features (User Requirements)

### 1. Web Interface
**Status:** ✅ Confirmed  
**Notes:** Browser-based app. Clean, professional UI. No desktop install required.

### 2. Topic Input
**Status:** ✅ Confirmed  
**Notes:** Natural language input. User describes business problem/goal in plain English.

---

## 🔍 Deep Research & Validation Engine

**Decision:** Web search only (no proprietary DBs)  
**Tools:** Perplexity API + Brave Search + SerpAPI

### 3. Storyline Architecture (Pyramid Principle + MECE)
**Status:** ✅ Confirmed  

**Core Logic:**
- **SCQA Framework:** Situation → Complication → Question → Answer
- **Bottom-Up Building:** Start with data points → Group into insights → Synthesize into the "So What?"
- **MECE Structure:** Ensure mutually exclusive, collectively exhaustive groupings
- **Governing Thought:** Single unifying message at the top
- **Key Line:** Supporting arguments that branch logically

**Implementation:**
- LLM agent for structure generation
- Constraint validation (MECE check)
- User feedback loop for storyline adjustment

### 4. Hypothesis-Driven Research
**Status:** ✅ Confirmed  

**Capabilities:**
- Generate 3-5 testable hypotheses based on topic
- Execute multi-source research:
  - Web search (industry reports, news, analyst data)
  - Financial databases (public APIs, SEC filings)
  - Academic/white paper references
- **Validate OR Disprove** each hypothesis with evidence
- Flag confidence levels per claim
- Cite all sources with links

**Research Depth Levels:**
| Level | Description | Time |
|-------|-------------|------|
| Quick | Top 5 sources, summary | 2-3 min |
| Standard | 10-15 sources, validation | 5-8 min |
| Deep | 20+ sources, hypothesis testing | 10-15 min |

---

## 📊 Slide Generation

### 5. Data-Heavy, Dense Slides
**Status:** ✅ Confirmed  

**Slide Types Supported:**
| Type | Use Case |
|------|----------|
| Executive Summary | Top-line message + 3 key takeaways |
| Situation/Context | Background data, market size, trends |
| Hypothesis Matrix | Tested hypotheses with confidence ratings |
| Data Tables | Financials, comparisons, benchmarks |
| Charts | Waterfall, bridge, tornado, scatter, heatmap |
| Framework | 2x2 matrix, value chain, BCG matrix |
| Recommendation | Clear next steps with owners + timelines |
| Appendix | Supporting data, methodology |

**Chart Types:**
- Waterfall (bridge) charts
- Marimekko (100% stacked with width)
- Tornado (sensitivity analysis)
- Scatter with quadrants
- Heatmaps
- Sankey diagrams
- Bubble charts (2-axis + size)

---

## 🎨 Design & Branding

### 6. Template System
**Status:** ✅ Confirmed  

**Default Template — "McKinsey Classic":**
- Font: Helvetica Neue / Arial (sans-serif)
- Colors: Deep blues, minimal accents
- Layout: Header + content + page number
- Logo placeholder (top right)
- Source line (bottom left)
- Chart styles: Clean, minimal gridlines

**User Upload:**
- Upload any .pptx file as master template
- Extract: color palette, fonts, layout masters, logo
- Apply styles to AI-generated slides

---

## 📤 Export

### 7. Export Formats
**Status:** ✅ Confirmed

| Format | Use Case | Implementation |
|--------|----------|----------------|
| PPTX | Editable, present in PowerPoint | python-pptx / Aspose |
| PDF | Static, email, review | LibreOffice / Aspose |
| JSON | API integration, further processing | Native |
| Markdown | Quick review, copy-paste | Native |

---

## 🤖 Quality Assurance

### 8. Quality Checker Agent
**Status:** ✅ Confirmed  

**Review Dimensions:**

| Check | Description | Severity |
|-------|-------------|----------|
| **Slide Logic** | Clear SCQA? Logical flow? | Critical |
| **MECE Validation** | Are groupings truly MECE? | Critical |
| **So What?** | Is there a clear insight? | Critical |
| **Data Quality** | Sources cited? Current data? | High |
| **Chart Accuracy** | Axes labeled? Scales correct? | High |
| **Visual Consistency** | Font sizes, colors, alignment | Medium |
| **Grammar/Style** | Professional tone, no jargon | Low |
| **Executability** | Can slides be presented as-is? | High |

**Output:**
- Scorecard (0-100)
- Action items to fix
- Suggested improvements
- Pass/Fail per slide

---

## 🏗️ Technical Architecture

### Stack Recommendation

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                             │
│  React + TypeScript + Tailwind CSS                       │
│  - Drag/drop slide reordering                           │
│  - Real-time preview                                     │
│  - Template upload (PPTX)                                │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                     BACKEND                                │
│  Python (FastAPI)                                        │
│  - API endpoints                                          │
│  - Job queue (Celery + Redis)                           │
│  - WebSocket for progress updates                       │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                  AI ENGINE                                 │
│  - GPT-4 / Claude for storyline/outlines                 │
│  - Perplexity API / Brave Search for research            │
│  - Fine-tuned models for consulting structure            │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│              SLIDE GENERATOR                               │
│  - python-pptx (Apache 2.0)                              │
│  - Custom chart generation (matplotlib → SVG → PPTX)       │
│  - Template parser (load user PPTX, extract styles)        │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│               QUALITY AGENT                                │
│  - Secondary LLM pass for review                           │
│  - Rule-based validation (MECE, SCQA)                     │
│  - Visual QA (font sizes, alignment checks)                │
└────────────────────────────────────────────────────────────┘
```

---

## 📅 Implementation Phases

### Phase 1: MVP (4-6 weeks)
**Goal:** One complete end-to-end flow

- [ ] Web UI: Topic input → Output preview
- [ ] Basic storyline generation (SCQA)
- [ ] Web research integration (5-10 sources)
- [ ] Generate 5-8 slides per deck
- [ ] 3 chart types (bar, line, waterfall)
- [ ] Export to PPTX (McKinsey default template)
- [ ] Basic quality checker (grammar + logic)

**Output:** Working demo, can present to stakeholders

---

### Phase 2: Production (4-6 weeks)
**Goal:** Daily-use tool

- [ ] User template upload (extract styles from PPTX)
- [ ] Advanced chart types (Marimekko, tornado, Sankey)
- [ ] Deep research mode (20+ sources, hypothesis testing)
- [ ] Quality checker agent v2 (MECE validation, confidence scoring)
- [ ] PDF export
- [ ] Slide editing UI (post-generation tweaks)
- [ ] History + save projects

---

### Phase 3: Scale (2-4 weeks)
**Goal:** Enterprise-ready

- [ ] API access (programmatic generation)
- [ ] Team collaboration (share decks, comments)
- [ ] Upload data files (CSV/Excel → auto-charts)
- [ ] Industry-specific templates (PE, tech, healthcare)
