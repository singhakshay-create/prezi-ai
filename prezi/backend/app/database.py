from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings
import os

# Ensure data directory exists
os.makedirs("./data", exist_ok=True)

# Database setup
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Job(Base):
    """Database model for presentation generation jobs."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    length = Column(String, nullable=False)
    llm_provider = Column(String, nullable=False)
    research_provider = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    progress = Column(Integer, default=0)
    message = Column(String, default="")
    error = Column(String, nullable=True)

    # Results (JSON fields)
    storyline = Column(JSON, nullable=True)
    research = Column(JSON, nullable=True)
    quality_score = Column(JSON, nullable=True)

    # Output
    pptx_path = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)

    # Template
    template_id = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Template(Base):
    """Database model for user-uploaded presentation templates."""
    __tablename__ = "templates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

    # Migrate: add columns to jobs table if they don't exist
    for col in ["pdf_path", "template_id"]:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"SELECT {col} FROM jobs LIMIT 1"))
        except Exception:
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} TEXT"))
                    conn.commit()
            except Exception:
                pass

    # Migrate: create templates table if it doesn't exist (handled by create_all above,
    # but explicit check for older DBs that may have been created before this table)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT id FROM templates LIMIT 1"))
    except Exception:
        Base.metadata.tables["templates"].create(bind=engine, checkfirst=True)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
