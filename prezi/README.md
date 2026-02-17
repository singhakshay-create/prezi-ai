# Prezi AI - MVP

AI-powered consulting presentation generator using Pyramid Principle, SCQA framework, and hypothesis-driven research.

## Features

- **Multi-Provider LLM Support**: Claude 3.5 Sonnet, OpenAI o1-pro/GPT-4o, Nvidia Kimi K2.5
- **Flexible Research**: Mock data, Perplexity, Brave Search, SerpAPI
- **SCQA Storyline**: Structured consulting narratives
- **Hypothesis-Driven**: Research validates testable hypotheses
- **Quality Scoring**: AI-powered quality assessment
- **Professional Slides**: McKinsey-style presentations with charts

## Quick Start

### Prerequisites

- Node.js 18+ (for frontend)
- At least one LLM API key (Anthropic, OpenAI, or Nvidia)
- Research API keys (optional - mock data available)

Python 3.11 is installed automatically via `uv` if not present.

### Setup

1. Create environment file:
```bash
cp .env.example .env
```

2. Add your API keys to `.env`:
```bash
# At minimum, add one LLM provider
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-proj-...
# or
NVIDIA_API_KEY=nvapi-...

# Optional: Add research providers (mock works by default)
SERP_API_KEY=...
BRAVE_API_KEY=...
PERPLEXITY_API_KEY=...
```

3. Start everything:
```bash
./start-local.sh
```

4. Open browser:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. Enter a business topic (e.g., "Should Company X enter the Indian EV market?")
2. Select deck length: Short (1-5 slides), Medium (6-15), or Long (16+)
3. Choose AI model and research source
4. Click "Generate Presentation"
5. Download PPTX file

## Architecture

```
prezi/
├── backend/          # FastAPI + python-pptx
│   └── app/
│       ├── agents/       # Storyline, Research, Slides, Quality
│       ├── providers/    # LLM and Research providers
│       ├── api/          # REST endpoints
│       └── tasks/        # Background task runner
├── frontend/         # React + TypeScript + Tailwind
│   └── src/
│       ├── components/   # UI components
│       └── services/     # API client
├── start-local.sh    # Start both services
└── .env              # API keys
```

## API Endpoints

### `GET /api/providers`
Get available LLM and research providers

### `POST /api/generate`
Start presentation generation
```json
{
  "topic": "Business question",
  "length": "medium",
  "llm_provider": "claude",
  "research_provider": "mock"
}
```

### `GET /api/status/{job_id}`
Poll job status (0-100% progress)

### `GET /api/download/{job_id}`
Download generated PPTX

### `GET /api/result/{job_id}`
Get full results with storyline, research, quality score

## Development

### Backend
```bash
source backend/.venv/bin/activate
uvicorn app.main:app --reload --app-dir backend
```

### Frontend
```bash
cd frontend
npm run dev
```

## Troubleshooting

### No providers available
- Check `.env` file has at least one API key
- Restart services with `./start-local.sh`

### Generation fails
- Check terminal output for backend errors
- Verify API keys are valid
- Check rate limits on API providers

## License

MIT
