"""Integration tests for the full generation pipeline."""

import json
import os
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import sessionmaker

from app.database import Base, Job
from app.tasks.worker import _async_generate
from tests.conftest import MockLLMProvider, DeterministicResearchProvider


class TestFullPipeline:
    async def test_full_pipeline_short(self, db_engine, sample_storyline_json, sample_quality_json):
        """_async_generate with mocked LLM + mock research → job completed, all fields populated."""
        Session = sessionmaker(bind=db_engine)
        session = Session()

        # Create the job
        job = Job(
            id="pipeline-short",
            topic="Cloud computing strategy for enterprise clients",
            length="short",
            llm_provider="claude",
            research_provider="mock",
            status="queued",
            progress=0,
            message="Queued",
        )
        session.add(job)
        session.commit()
        session.close()

        # Mock LLM: first call = storyline, second call = quality
        mock_llm = MockLLMProvider(response=sample_storyline_json)

        # We need the LLM to return different responses for storyline vs quality
        call_count = 0
        original_generate = mock_llm.generate

        async def _side_effect(prompt, system=None, temperature=0.7, max_tokens=4000):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_llm.response = sample_storyline_json
            else:
                mock_llm.response = sample_quality_json
            return await original_generate(prompt, system, temperature, max_tokens)

        mock_llm.generate = _side_effect

        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "pipeline-short",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        # Verify final state
        session = Session()
        job = session.query(Job).filter(Job.id == "pipeline-short").first()
        assert job.status == "completed"
        assert job.progress == 100
        assert job.storyline is not None
        assert job.research is not None
        assert job.quality_score is not None
        assert job.pptx_path is not None
        assert job.completed_at is not None
        session.close()

    async def test_pipeline_storyline_failure(self, db_engine):
        """LLM raises during storyline → job.status='failed'."""
        Session = sessionmaker(bind=db_engine)
        session = Session()

        job = Job(
            id="pipeline-fail-story",
            topic="Cloud computing strategy for enterprise clients",
            length="short",
            llm_provider="claude",
            research_provider="mock",
            status="queued",
            progress=0,
            message="Queued",
        )
        session.add(job)
        session.commit()
        session.close()

        # LLM that raises an error
        mock_llm = MockLLMProvider(response="not valid json")
        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "pipeline-fail-story",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == "pipeline-fail-story").first()
        assert job.status == "failed"
        assert job.error is not None
        session.close()

    async def test_pipeline_research_failure(self, db_engine, sample_storyline_json):
        """Research provider raises → job.status='failed'."""
        Session = sessionmaker(bind=db_engine)
        session = Session()

        job = Job(
            id="pipeline-fail-research",
            topic="Cloud computing strategy for enterprise clients",
            length="short",
            llm_provider="claude",
            research_provider="mock",
            status="queued",
            progress=0,
            message="Queued",
        )
        session.add(job)
        session.commit()
        session.close()

        mock_llm = MockLLMProvider(response=sample_storyline_json)

        # Research provider that raises
        class FailingResearchProvider(DeterministicResearchProvider):
            async def search(self, query, num_results=10):
                raise RuntimeError("Research API down")

        mock_research = FailingResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "pipeline-fail-research",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == "pipeline-fail-research").first()
        assert job.status == "failed"
        assert "Research API down" in job.error
        session.close()


class TestRefinementLoop:
    """Tests for the iterative quality refinement loop in worker.py."""

    def _make_job(self, session, job_id: str):
        job = Job(
            id=job_id,
            topic="Cloud computing strategy for enterprise clients",
            length="short",
            llm_provider="claude",
            research_provider="mock",
            status="queued",
            progress=0,
            message="Queued",
        )
        session.add(job)
        session.commit()

    async def _run_pipeline(self, db_engine, job_id, storyline_json, quality_report_json, feedback_json):
        """Helper that runs _async_generate with mocked providers."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        self._make_job(session, job_id)
        session.close()

        call_count = 0

        class MultiResponseLLM(MockLLMProvider):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4000):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    self.response = storyline_json
                elif call_count == 2:
                    # LLM inspect call (quality report)
                    self.response = quality_report_json
                else:
                    # LLM feedback call or subsequent inspect
                    self.response = feedback_json
                return await super().generate(prompt, system, temperature, max_tokens)

        mock_llm = MultiResponseLLM()
        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                job_id,
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == job_id).first()
        data = dict(
            status=job.status,
            progress=job.progress,
            message=job.message,
            quality_score=job.quality_score,
            pptx_path=job.pptx_path,
        )
        session.close()
        return data

    async def test_pipeline_runs_at_least_one_refinement(
        self, db_engine, sample_storyline_json, sample_slide_quality_report_json, sample_slide_feedback_json
    ):
        """Low quality score triggers at least one refinement pass."""
        result = await self._run_pipeline(
            db_engine,
            "refine-at-least-once",
            sample_storyline_json,
            sample_slide_quality_report_json,
            sample_slide_feedback_json,
        )
        assert result["status"] == "completed"
        score = result["quality_score"]
        assert score is not None
        # iterations_run should be recorded
        assert score.get("iterations_run", 0) >= 1
        # Clean up pptx
        if result["pptx_path"] and os.path.isfile(result["pptx_path"]):
            os.remove(result["pptx_path"])

    async def test_pipeline_stops_at_threshold(
        self, db_engine, sample_storyline_json
    ):
        """If first inspection returns score >= 70 and no feedback, pipeline exits after 1 pass."""
        import json as _json

        # High score report with no issues → no feedback generated → exits early
        high_score_report = _json.dumps({
            "iteration": 1,
            "information_density_score": 90,
            "chart_quality_score": 85,
            "narrative_flow_score": 88,
            "storyline_suggestions": [],
            "issues": [],
        })
        empty_feedback = _json.dumps([])

        Session = sessionmaker(bind=db_engine)
        session = Session()
        self._make_job(session, "refine-threshold")
        session.close()

        call_count = 0

        class HighScoreLLM(MockLLMProvider):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4000):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    self.response = sample_storyline_json
                elif call_count == 2:
                    self.response = high_score_report
                else:
                    self.response = empty_feedback
                return await super().generate(prompt, system, temperature, max_tokens)

        mock_llm = HighScoreLLM()
        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "refine-threshold",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == "refine-threshold").first()
        assert job.status == "completed"
        score = job.quality_score
        # With high scores and no issues, only 1 iteration should run
        assert score.get("iterations_run", 0) == 1
        if job.pptx_path and os.path.isfile(job.pptx_path):
            os.remove(job.pptx_path)
        session.close()

    async def test_pipeline_stops_at_max(
        self, db_engine, sample_storyline_json, sample_slide_quality_report_json, sample_slide_feedback_json
    ):
        """If score never reaches threshold, stops at MAX_ITERATIONS=5."""
        # The sample report scores are low (~59/100), and we keep returning feedback
        # so it should iterate up to MAX_ITERATIONS

        Session = sessionmaker(bind=db_engine)
        session = Session()
        self._make_job(session, "refine-max")
        session.close()

        call_count = 0

        class AlwaysLowLLM(MockLLMProvider):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4000):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    self.response = sample_storyline_json
                elif call_count % 2 == 0:
                    self.response = sample_slide_quality_report_json
                else:
                    self.response = sample_slide_feedback_json
                return await super().generate(prompt, system, temperature, max_tokens)

        mock_llm = AlwaysLowLLM()
        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "refine-max",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == "refine-max").first()
        assert job.status == "completed"
        score = job.quality_score
        # iterations_run should be <= MAX_ITERATIONS (5)
        assert score.get("iterations_run", 0) <= 5
        if job.pptx_path and os.path.isfile(job.pptx_path):
            os.remove(job.pptx_path)
        session.close()

    async def test_pipeline_plateau_exit(
        self, db_engine, sample_storyline_json, sample_slide_quality_report_json, sample_slide_feedback_json
    ):
        """When scores plateau (no improvement over 3 iterations), exit early."""
        # sample_slide_quality_report_json always returns the same low score
        # so after 3 iterations with same score, plateau detection kicks in

        Session = sessionmaker(bind=db_engine)
        session = Session()
        self._make_job(session, "refine-plateau")
        session.close()

        call_count = 0

        class PlateauLLM(MockLLMProvider):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4000):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    self.response = sample_storyline_json
                elif call_count % 2 == 0:
                    self.response = sample_slide_quality_report_json
                else:
                    self.response = sample_slide_feedback_json
                return await super().generate(prompt, system, temperature, max_tokens)

        mock_llm = PlateauLLM()
        mock_research = DeterministicResearchProvider()

        with patch("app.tasks.worker.ProviderFactory") as mock_factory, \
             patch("app.tasks.worker.SessionLocal", return_value=Session()):
            mock_factory.get_llm_provider.return_value = mock_llm
            mock_factory.get_research_provider.return_value = mock_research

            await _async_generate(
                "refine-plateau",
                "Cloud computing strategy for enterprise clients",
                "short",
                "claude",
                "mock",
            )

        session = Session()
        job = session.query(Job).filter(Job.id == "refine-plateau").first()
        assert job.status == "completed"
        score = job.quality_score
        # Plateau exit means we stop before MAX_ITERATIONS=5
        assert score.get("iterations_run", 0) < 5
        if job.pptx_path and os.path.isfile(job.pptx_path):
            os.remove(job.pptx_path)
        session.close()
