"""Integration tests for the full generation pipeline."""

import json
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
