"""Integration tests for database Job CRUD operations."""

import json
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, Job


class TestJobCRUD:
    def test_create_job(self, db_session):
        """Insert Job, verify all fields persist."""
        job = Job(
            id="test-123",
            topic="Cloud computing strategy analysis",
            length="medium",
            llm_provider="claude",
            research_provider="mock",
            status="queued",
            progress=0,
            message="Job queued...",
        )
        db_session.add(job)
        db_session.commit()

        saved = db_session.query(Job).filter(Job.id == "test-123").first()
        assert saved is not None
        assert saved.topic == "Cloud computing strategy analysis"
        assert saved.length == "medium"
        assert saved.status == "queued"

    def test_query_by_id(self, db_session):
        """Retrieve by primary key."""
        job = Job(
            id="pk-test",
            topic="A valid business topic for testing",
            length="short",
            llm_provider="claude",
            research_provider="mock",
        )
        db_session.add(job)
        db_session.commit()

        result = db_session.get(Job, "pk-test")
        assert result is not None
        assert result.id == "pk-test"

    def test_update_status(self, db_session):
        """Update status and verify persistence."""
        job = Job(
            id="update-test",
            topic="Testing status update flow here",
            length="long",
            llm_provider="openai",
            research_provider="mock",
            status="queued",
        )
        db_session.add(job)
        db_session.commit()

        job.status = "completed"
        job.progress = 100
        db_session.commit()

        refreshed = db_session.query(Job).filter(Job.id == "update-test").first()
        assert refreshed.status == "completed"
        assert refreshed.progress == 100

    def test_json_fields_roundtrip(self, db_session):
        """Set/get storyline, research, quality_score JSON fields."""
        storyline_data = {"scqa": {"situation": "test"}, "hypotheses": []}
        research_data = {"hypotheses_evidence": [], "total_sources": 0}
        quality_data = {"overall_score": 85, "suggestions": ["Improve"]}

        job = Job(
            id="json-test",
            topic="JSON roundtrip testing for all fields",
            length="short",
            llm_provider="claude",
            research_provider="mock",
            storyline=storyline_data,
            research=research_data,
            quality_score=quality_data,
        )
        db_session.add(job)
        db_session.commit()

        saved = db_session.query(Job).filter(Job.id == "json-test").first()
        assert saved.storyline["scqa"]["situation"] == "test"
        assert saved.research["total_sources"] == 0
        assert saved.quality_score["overall_score"] == 85

    def test_init_db_creates_tables(self):
        """Base.metadata.create_all on a fresh engine creates the jobs table."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        # Should be able to query without error
        result = session.query(Job).all()
        assert result == []
        session.close()
        engine.dispose()
