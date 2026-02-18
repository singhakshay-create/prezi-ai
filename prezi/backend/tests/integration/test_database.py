"""Integration tests for database Job CRUD operations."""

import json
import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, Job, init_db


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

    def test_migration_adds_missing_columns(self, monkeypatch):
        """Regression: init_db() migrates an old jobs table missing pdf_path/template_id.

        This reproduces the bug where SQLAlchemy 2.x requires text() for raw SQL,
        causing the migration to silently fail and leaving the jobs table without
        pdf_path and template_id columns, which then caused:
            sqlite3.OperationalError: table jobs has no column named pdf_path
        on every INSERT — surfacing as "Failed to start generation" in the UI.
        """
        engine = create_engine("sqlite:///:memory:")

        # Simulate an old database: create the jobs table WITHOUT the new columns
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE jobs (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    length TEXT NOT NULL,
                    llm_provider TEXT NOT NULL,
                    research_provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER,
                    message TEXT,
                    error TEXT,
                    storyline JSON,
                    research JSON,
                    quality_score JSON,
                    pptx_path TEXT,
                    created_at DATETIME,
                    completed_at DATETIME
                )
            """))
            conn.execute(text("""
                CREATE TABLE templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at DATETIME
                )
            """))
            conn.commit()

        # Patch the module-level engine used by init_db so it targets our in-memory DB
        import app.database as db_module
        original_engine = db_module.engine
        db_module.engine = engine
        try:
            init_db()
        finally:
            db_module.engine = original_engine

        # Both columns must now exist — a full INSERT should succeed without error
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            job = Job(
                id="migration-test",
                topic="Regression test for missing columns",
                length="short",
                llm_provider="claude",
                research_provider="mock",
                status="queued",
                progress=0,
                message="Testing",
                pdf_path=None,
                template_id=None,
            )
            session.add(job)
            session.commit()  # This raised OperationalError before the fix

            saved = session.query(Job).filter(Job.id == "migration-test").first()
            assert saved is not None
            assert saved.pdf_path is None
            assert saved.template_id is None
        finally:
            session.close()
            engine.dispose()
