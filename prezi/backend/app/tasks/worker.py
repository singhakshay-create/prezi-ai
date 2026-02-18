"""In-process background task runner (no Celery/Redis needed)."""

import asyncio
import threading
from app.config import settings
from app.providers import ProviderFactory
from app.agents.storyline import StorylineGenerator
from app.agents.research import ResearchEngine
from app.agents.slides import SlideGenerator
from app.agents.quality import QualityChecker
from app.agents.image_gen import ImageGenerator
from app.database import SessionLocal, Job, Template
from app.ws.manager import notify_progress
from typing import Optional
from datetime import datetime


def generate_presentation_background(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str,
    template_id: Optional[str] = None,
):
    """Run presentation generation in a background thread."""
    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, topic, length, llm_provider, research_provider, template_id),
        daemon=True
    )
    thread.start()


def _run_generation(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str,
    template_id: Optional[str] = None,
):
    """Execute the generation pipeline synchronously in a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _async_generate(job_id, topic, length, llm_provider, research_provider, template_id)
        )
    finally:
        loop.close()


async def _async_generate(
    job_id: str,
    topic: str,
    length: str,
    llm_provider: str,
    research_provider: str,
    template_id: Optional[str] = None,
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

        # Look up template path
        template_path = None
        if template_id and template_id != "default":
            template = db.query(Template).filter(Template.id == template_id).first()
            if template:
                template_path = template.path

        PASS_THRESHOLD = 70
        MAX_ITERATIONS = 5

        image_gen = ImageGenerator(openai_api_key=settings.OPENAI_API_KEY)
        slides_agent = SlideGenerator(template_path=template_path, image_generator=image_gen)
        quality_agent = QualityChecker(llm)

        # Initial slide generation
        pptx_path = await slides_agent.create_presentation(
            topic, storyline, research, length
        )

        score_history = []
        last_score = None
        last_report = None

        for iteration in range(1, MAX_ITERATIONS + 1):
            iter_progress = 65 + iteration * 5  # 70, 75, 80, 85, 90

            job.status = "refining"
            job.progress = iter_progress - 2
            job.message = f"Quality review (pass {iteration}/{MAX_ITERATIONS})..."
            db.commit()
            _notify()

            last_score, last_report, feedback = await quality_agent.check_with_pptx(
                pptx_path, storyline, research, iteration
            )
            score_history.append(last_score.overall_score)

            if last_score.overall_score >= PASS_THRESHOLD or not feedback:
                break

            # Plateau detection: no improvement after 3 iterations
            if len(score_history) >= 3 and score_history[-1] <= score_history[-2]:
                break

            job.progress = iter_progress
            job.message = f"Refining slides (pass {iteration}/{MAX_ITERATIONS})..."
            db.commit()
            _notify()

            pptx_path = await slides_agent.refine_presentation(
                topic, storyline, research, length, feedback, iteration
            )

        last_score.iterations_run = len(score_history)
        last_score.final_report = last_report

        job.pptx_path = pptx_path
        job.quality_score = last_score.dict()
        job.progress = 100
        job.status = "completed"
        job.message = f"Done. {len(score_history)} refinement pass(es). Score: {last_score.overall_score}/100"
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
