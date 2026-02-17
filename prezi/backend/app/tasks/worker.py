"""In-process background task runner (no Celery/Redis needed)."""

import asyncio
import threading
from app.config import settings
from app.providers import ProviderFactory
from app.agents.storyline import StorylineGenerator
from app.agents.research import ResearchEngine
from app.agents.slides import SlideGenerator
from app.agents.quality import QualityChecker
from app.database import SessionLocal, Job
from app.ws.manager import notify_progress
from datetime import datetime


def generate_presentation_background(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str
):
    """Run presentation generation in a background thread."""
    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, topic, length, llm_provider, research_provider),
        daemon=True
    )
    thread.start()


def _run_generation(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str
):
    """Execute the generation pipeline synchronously in a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _async_generate(job_id, topic, length, llm_provider, research_provider)
        )
    finally:
        loop.close()


async def _async_generate(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str
):
    """Async presentation generation pipeline."""
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        def _notify():
            notify_progress(job_id, {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error": job.error,
            })

        # Update status: storyline generation
        job.status = "storyline"
        job.progress = 10
        job.message = "Generating storyline..."
        db.commit()
        _notify()

        # 1. Initialize providers
        llm = ProviderFactory.get_llm_provider(llm_provider)
        research_api = ProviderFactory.get_research_provider(research_provider)

        # 2. Generate storyline
        storyline_agent = StorylineGenerator(llm)
        storyline = await storyline_agent.generate(topic, length)

        job.storyline = storyline.dict()
        job.progress = 30
        job.message = "Storyline generated. Starting research..."
        db.commit()
        _notify()

        # 3. Research hypotheses
        job.status = "researching"
        job.progress = 35
        job.message = f"Researching {len(storyline.hypotheses)} hypotheses..."
        db.commit()
        _notify()

        research_agent = ResearchEngine(research_api)
        research = await research_agent.validate_hypotheses(storyline.hypotheses)

        job.research = research.dict()
        job.progress = 60
        job.message = "Research complete. Generating slides..."
        db.commit()
        _notify()

        # 4. Generate slides
        job.status = "slides"
        job.progress = 65
        job.message = "Creating presentation slides..."
        db.commit()
        _notify()

        slides_agent = SlideGenerator()
        pptx_path = await slides_agent.create_presentation(
            topic, storyline, research, length
        )

        job.pptx_path = pptx_path
        job.progress = 85
        job.message = "Slides created. Running quality check..."
        db.commit()
        _notify()

        # 5. Quality check
        job.status = "quality"
        job.progress = 90
        job.message = "Evaluating presentation quality..."
        db.commit()
        _notify()

        quality_agent = QualityChecker(llm)
        quality_score = await quality_agent.check(storyline)

        job.quality_score = quality_score.dict()
        job.progress = 100
        job.status = "completed"
        job.message = f"Completed! Quality score: {quality_score.overall_score}/100"
        job.completed_at = datetime.utcnow()
        db.commit()
        _notify()

    except Exception as e:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.message = f"Failed: {str(e)}"
            db.commit()
            notify_progress(job_id, {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error": job.error,
            })

    finally:
        db.close()
