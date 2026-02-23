"""In-process background task runner (no Celery/Redis needed)."""

import asyncio
import logging
import threading
import traceback
from app.config import settings

logger = logging.getLogger("prezi.worker")
from app.providers import ProviderFactory
from app.agents.storyline import StorylineGenerator
from app.agents.research import ResearchEngine
from app.agents.query_expander import QueryExpander
from app.agents.slides import SlideGenerator
from app.agents.quality import QualityChecker
try:
    from app.agents.html_renderer import HtmlSlideGenerator
    _HTML_RENDERER_AVAILABLE = True
except ImportError:
    _HTML_RENDERER_AVAILABLE = False
from app.database import SessionLocal, Job, Template
from app.ws.manager import notify_progress
from typing import Optional
from datetime import datetime


def _llm_timeout_secs(provider: str) -> int:
    """LLM read timeout in seconds — Kimi K2 thinking mode can take several minutes."""
    return 600 if provider.lower() == "nvidia" else 120


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

        def _notify(**extra):
            notify_progress(job_id, {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error": job.error,
                "ts": datetime.utcnow().isoformat() + "Z",
                **extra,
            })

        # Step 1: Init providers
        job.status = "expanding"
        job.progress = 3
        job.message = f"Initializing providers ({llm_provider} + {research_provider})..."
        db.commit()
        _notify()

        llm = ProviderFactory.get_llm_provider(llm_provider)
        research_api = ProviderFactory.get_research_provider(research_provider)
        logger.info(f"Job {job_id}: providers initialized ({llm_provider}, {research_provider})")

        # Step 2: Query expansion
        expander = QueryExpander(llm)
        job.progress = 5
        job.message = f"→ Querying {llm_provider}: expanding research brief..."
        db.commit()
        _notify(
            timeout_seconds=_llm_timeout_secs(llm_provider),
            query_preview=f"Topic: \"{topic}\" · Length: {length}",
        )

        _t0 = datetime.utcnow()
        expanded_brief = await expander.expand(topic, length)
        _elapsed = round((datetime.utcnow() - _t0).total_seconds())
        logger.info(f"Job {job_id}: query expansion complete ({len(expanded_brief)} chars, {_elapsed}s)")

        job.message = f"← {llm_provider} responded in {_elapsed}s — research brief ready"
        db.commit()
        _notify()

        # Step 3: Storyline generation
        job.status = "storyline"
        job.progress = 10
        storyline_agent = StorylineGenerator(llm)
        job.message = f"→ Querying {llm_provider}: generating SCQA storyline..."
        db.commit()
        _notify(
            timeout_seconds=_llm_timeout_secs(llm_provider),
            query_preview=expanded_brief[:300].replace('\n', ' ').strip() + ("..." if len(expanded_brief) > 300 else ""),
        )

        _t0 = datetime.utcnow()
        storyline = await storyline_agent.generate(topic, length, expanded_brief)
        _elapsed = round((datetime.utcnow() - _t0).total_seconds())
        logger.info(f"Job {job_id}: storyline done ({len(storyline.hypotheses)} hypotheses, {_elapsed}s)")

        job.storyline = storyline.dict()
        job.progress = 30
        job.message = f"← {llm_provider} responded in {_elapsed}s — {len(storyline.hypotheses)} hypotheses"
        db.commit()
        _notify()

        # Step 4: Research
        job.status = "researching"
        job.progress = 35
        research_agent = ResearchEngine(research_api)
        job.message = f"→ Researching {len(storyline.hypotheses)} hypotheses via {research_provider}..."
        db.commit()
        _notify()

        _t0 = datetime.utcnow()
        research = await research_agent.validate_hypotheses(storyline.hypotheses, expanded_brief)
        _elapsed = round((datetime.utcnow() - _t0).total_seconds())
        logger.info(f"Job {job_id}: research done ({research.total_sources} sources, {_elapsed}s)")

        job.research = research.dict()
        job.progress = 60
        job.message = f"← Research complete in {_elapsed}s — {research.total_sources} sources found"
        db.commit()
        _notify()

        # Step 5: Slides
        job.status = "slides"
        job.progress = 65
        job.message = "[4/5] Rendering presentation slides (HTML → PNG → PPTX)..."
        db.commit()
        _notify()
        logger.info(f"Job {job_id}: starting slide generation")

        # Look up template path
        template_path = None
        if template_id and template_id != "default":
            template = db.query(Template).filter(Template.id == template_id).first()
            if template:
                template_path = template.path

        await _run_slides_and_quality(job, storyline, research, llm, template_path, db, _notify, llm_provider)

    except Exception as e:
        logger.exception(f"Job {job_id} failed during pipeline")
        err_type = type(e).__name__
        err_detail = str(e) or repr(e) or "(no detail)"
        err_msg = f"{err_type}: {err_detail}"
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = err_msg
            job.message = f"Failed — {err_msg}"
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


async def _run_slides_and_quality(job, storyline, research, llm, template_path, db, notify, llm_provider_name: str = "LLM"):
    """Shared: runs SlideGenerator + iterative quality refinement."""
    from app.models import Storyline as StorylineModel, ResearchResults as ResearchModel

    PASS_THRESHOLD = 70
    MAX_ITERATIONS = 5

    from app.agents.image_gen import ImageGenerator
    image_gen = ImageGenerator(openai_api_key=getattr(settings, "OPENAI_API_KEY", None))

    slides_agent = SlideGenerator(template_path=template_path, image_gen=image_gen)
    quality_agent = QualityChecker(llm)

    # Ensure we have proper model objects (may be plain dicts when loaded from DB)
    if isinstance(storyline, dict):
        storyline = StorylineModel(**storyline)
    if isinstance(research, dict):
        research = ResearchModel(**research)

    # Initial slide generation
    pptx_path = await slides_agent.create_presentation(
        job.topic, storyline, research, job.length
    )

    score_history = []
    last_score = None
    last_report = None

    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_progress = 65 + iteration * 5  # 70, 75, 80, 85, 90

        job.status = "refining"
        job.progress = iter_progress - 2
        job.message = f"→ Quality check pass {iteration}/{MAX_ITERATIONS}: querying {llm_provider_name}..."
        db.commit()
        notify(
            timeout_seconds=_llm_timeout_secs(llm_provider_name),
            query_preview=f"Reviewing slide quality and MECE structure (iteration {iteration}/{MAX_ITERATIONS})",
        )

        _t0 = datetime.utcnow()
        last_score, last_report, feedback = await quality_agent.check_with_pptx(
            pptx_path, storyline, research, iteration
        )
        _elapsed = round((datetime.utcnow() - _t0).total_seconds())
        score_history.append(last_score.overall_score)

        job.message = f"← Quality score: {last_score.overall_score}/100 ({_elapsed}s, pass {iteration})"
        db.commit()
        notify()

        if last_score.overall_score >= PASS_THRESHOLD or not feedback:
            break

        # Plateau detection: no improvement after 3 iterations
        if len(score_history) >= 3 and score_history[-1] <= score_history[-2]:
            break

        job.progress = iter_progress
        job.message = f"→ Refining slides pass {iteration}/{MAX_ITERATIONS}: querying {llm_provider_name}..."
        db.commit()
        notify(
            timeout_seconds=_llm_timeout_secs(llm_provider_name),
            query_preview=f"Applying quality feedback to regenerate slides (iteration {iteration}/{MAX_ITERATIONS})",
        )

        _t0 = datetime.utcnow()
        pptx_path = await slides_agent.refine_presentation(
            job.topic, storyline, research, job.length, feedback, iteration
        )
        _elapsed = round((datetime.utcnow() - _t0).total_seconds())
        job.message = f"← Slide refinement done (pass {iteration}, {_elapsed}s)"
        db.commit()
        notify()

    last_score.iterations_run = len(score_history)
    last_score.final_report = last_report

    job.pptx_path = pptx_path
    job.quality_score = last_score.dict()
    job.progress = 100
    job.status = "completed"
    job.message = f"Done. {len(score_history)} refinement pass(es). Score: {last_score.overall_score}/100"
    job.completed_at = datetime.utcnow()
    db.commit()
    notify()


def regenerate_slides_background(job_id: str):
    """Run slides+quality regeneration in a background thread."""
    thread = threading.Thread(target=_run_regen, args=(job_id,), daemon=True)
    thread.start()


def _run_regen(job_id: str):
    """Execute regen pipeline synchronously in a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_regenerate_slides(job_id))
    finally:
        loop.close()


async def _async_regenerate_slides(job_id: str):
    """Async slides-only regeneration pipeline — reuses persisted storyline+research."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        def _notify(**extra):
            notify_progress(job_id, {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error": job.error,
                "ts": datetime.utcnow().isoformat() + "Z",
                **extra,
            })

        job.status = "slides"
        job.progress = 65
        job.message = "Creating presentation slides..."
        db.commit()
        _notify()

        llm = ProviderFactory.get_llm_provider(job.llm_provider)

        # Look up template path
        template_path = None
        if job.template_id and job.template_id != "default":
            template = db.query(Template).filter(Template.id == job.template_id).first()
            if template:
                template_path = template.path

        await _run_slides_and_quality(job, job.storyline, job.research, llm, template_path, db, _notify, job.llm_provider or "LLM")

    except Exception as e:
        logger.exception(f"Regen job {job_id} failed")
        err_msg = f"{type(e).__name__}: {str(e) or repr(e)}"
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = err_msg
            job.message = f"Failed — {err_msg}"
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
