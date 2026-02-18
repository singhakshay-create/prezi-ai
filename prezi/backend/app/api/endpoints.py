from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models import (
    GenerateRequest,
    GenerateResponse,
    ProvidersResponse,
    ProviderInfo,
    JobStatus,
    JobSummary,
    JobListResponse,
    TemplateInfo,
    TemplateListResponse,
)
from app.database import get_db, Job, Template
from app.config import settings
from app.tasks.worker import generate_presentation_background
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from sqlalchemy import func

router = APIRouter()


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """Get available LLM and research providers."""
    return ProvidersResponse(
        llm_providers=[ProviderInfo(**p) for p in settings.available_llm_providers],
        research_providers=[ProviderInfo(**p) for p in settings.available_research_providers]
    )


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(db: Session = Depends(get_db)):
    """List all available templates."""
    templates = [
        TemplateInfo(
            id="default",
            name="McKinsey Classic",
            filename="default",
            created_at="",
        )
    ]

    db_templates = db.query(Template).order_by(Template.created_at.desc()).all()
    for t in db_templates:
        templates.append(
            TemplateInfo(
                id=t.id,
                name=t.name,
                filename=t.filename,
                created_at=t.created_at.isoformat() if t.created_at else "",
            )
        )

    return TemplateListResponse(templates=templates)


@router.post("/templates/upload", response_model=TemplateInfo)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a custom PPTX template."""
    if not file.filename or not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are allowed")

    # Read file content
    content = await file.read()

    # Validate it's a real PPTX
    try:
        from pptx import Presentation as PptxPresentation
        import io
        PptxPresentation(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PPTX file")

    # Save to disk
    template_id = str(uuid.uuid4())
    os.makedirs("./data/templates", exist_ok=True)
    save_path = f"./data/templates/{template_id}.pptx"
    with open(save_path, "wb") as f:
        f.write(content)

    # Save to DB
    template = Template(
        id=template_id,
        name=name,
        filename=file.filename,
        path=save_path,
    )
    db.add(template)
    db.commit()

    return TemplateInfo(
        id=template.id,
        name=template.name,
        filename=template.filename,
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete an uploaded template."""
    if template_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the default template")

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Remove file from disk
    if template.path and os.path.isfile(template.path):
        os.remove(template.path)

    db.delete(template)
    db.commit()

    return {"status": "deleted"}


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    """List all jobs with pagination."""
    total = db.query(func.count(Job.id)).scalar()
    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    summaries = []
    for job in jobs:
        quality_overall = None
        if job.quality_score and isinstance(job.quality_score, dict):
            quality_overall = job.quality_score.get("overall_score")

        summaries.append(
            JobSummary(
                job_id=job.id,
                topic=job.topic,
                length=job.length,
                status=job.status,
                progress=job.progress,
                quality_score_overall=quality_overall,
                error=job.error,
                created_at=job.created_at.isoformat() if job.created_at else "",
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
            )
        )

    return JobListResponse(jobs=summaries, total=total, page=page, per_page=per_page)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """Start presentation generation job."""

    # Validate providers are available
    llm_ids = [p["id"] for p in settings.available_llm_providers if p["available"]]
    research_ids = [p["id"] for p in settings.available_research_providers if p["available"]]

    if request.llm_provider not in llm_ids:
        raise HTTPException(
            status_code=400,
            detail=f"LLM provider '{request.llm_provider}' not available. Configure API key first."
        )

    if request.research_provider not in research_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Research provider '{request.research_provider}' not available."
        )

    # Create job
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        topic=request.topic,
        length=request.length,
        llm_provider=request.llm_provider,
        research_provider=request.research_provider,
        template_id=request.template_id,
        status="queued",
        progress=0,
        message="Job queued..."
    )

    db.add(job)
    db.commit()

    # Start background task (in-process, no Celery/Redis needed)
    generate_presentation_background(
        job_id,
        request.topic,
        request.length,
        request.llm_provider,
        request.research_provider,
        request.template_id,
    )

    return GenerateResponse(job_id=job_id)


@router.post("/retry/{job_id}", response_model=GenerateResponse)
async def retry_job(job_id: str, db: Session = Depends(get_db)):
    """Retry a failed job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed jobs. Current status: {job.status}"
        )
    job.status = "queued"
    job.progress = 0
    job.message = "Job queued (retry)..."
    job.error = None
    job.completed_at = None
    db.commit()
    generate_presentation_background(
        job_id, job.topic, job.length, job.llm_provider, job.research_provider,
        job.template_id,
    )
    return GenerateResponse(job_id=job_id)


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        error=job.error
    )


@router.get("/download/{job_id}")
async def download(job_id: str, db: Session = Depends(get_db)):
    """Download generated presentation."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Status: {job.status}"
        )

    if not job.pptx_path:
        raise HTTPException(status_code=500, detail="Presentation file not found")

    return FileResponse(
        job.pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"presentation_{job_id}.pptx"
    )


@router.get("/download/{job_id}/pdf")
async def download_pdf(job_id: str, db: Session = Depends(get_db)):
    """Download presentation as PDF (requires LibreOffice)."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Status: {job.status}"
        )

    if not job.pptx_path:
        raise HTTPException(status_code=500, detail="Presentation file not found")

    # Serve cached PDF if available
    if job.pdf_path and os.path.isfile(job.pdf_path):
        return FileResponse(
            job.pdf_path,
            media_type="application/pdf",
            filename=f"presentation_{job_id}.pdf"
        )

    # Check LibreOffice availability
    if not shutil.which("soffice"):
        raise HTTPException(
            status_code=503,
            detail="PDF export requires LibreOffice (soffice) to be installed"
        )

    # Convert PPTX to PDF
    outdir = os.path.dirname(job.pptx_path)
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, job.pptx_path],
            timeout=60,
            check=True,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")

    pdf_path = os.path.splitext(job.pptx_path)[0] + ".pdf"
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=500, detail="PDF file was not created")

    job.pdf_path = pdf_path
    db.commit()

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"presentation_{job_id}.pdf"
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str, db: Session = Depends(get_db)):
    """Get full job result with storyline, research, and quality score."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Status: {job.status}"
        )

    return {
        "job_id": job.id,
        "topic": job.topic,
        "length": job.length,
        "storyline": job.storyline,
        "research": job.research,
        "quality_score": job.quality_score,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }
