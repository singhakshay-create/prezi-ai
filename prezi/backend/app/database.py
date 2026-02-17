from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Float
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

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

    # Migrate: add pdf_path column if it doesn't exist
    try:
        with engine.connect() as conn:
            conn.execute("SELECT pdf_path FROM jobs LIMIT 1")
    except Exception:
        try:
            with engine.connect() as conn:
                conn.execute("ALTER TABLE jobs ADD COLUMN pdf_path TEXT")
        except Exception:
            pass


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
