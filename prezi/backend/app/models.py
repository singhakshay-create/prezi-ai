from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime


# API Request/Response Models

class SlideContent(BaseModel):
    slide_index: int
    title: str
    body_text: List[str]
    has_chart: bool
    has_table: bool
    shape_count: int
    word_count: int


class SlideIssue(BaseModel):
    slide_index: int
    issue_type: Literal[
        "too_sparse", "too_dense", "placeholder_data",
        "missing_so_what", "mece_violation", "weak_title",
        "missing_chart", "narrative_gap"
    ]
    description: str
    fix_suggestion: str


class SlideQualityReport(BaseModel):
    iteration: int
    slides: List[SlideContent]
    issues: List[SlideIssue]
    information_density_score: int
    chart_quality_score: int
    narrative_flow_score: int
    storyline_suggestions: List[str]


class SlideFeedback(BaseModel):
    slide_index: int
    new_title: Optional[str] = None
    new_bullets: Optional[List[str]] = None
    new_chart_data: Optional[dict] = None
    issues_addressed: List[str]


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=10, max_length=500)
    length: Literal["short", "medium", "long"]
    llm_provider: str = Field(..., description="LLM provider ID")
    research_provider: str = Field(default="mock", description="Research provider ID")
    template_id: Optional[str] = Field(default=None, description="Template ID (null for default)")


class GenerateResponse(BaseModel):
    job_id: str


class ProviderInfo(BaseModel):
    id: str
    name: str
    available: bool
    description: str


class ProvidersResponse(BaseModel):
    llm_providers: List[ProviderInfo]
    research_providers: List[ProviderInfo]


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "storyline", "researching", "slides", "quality", "refining", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    message: str
    error: Optional[str] = None


# Domain Models

class SCQAFramework(BaseModel):
    situation: str
    complication: str
    question: str
    answer: str


class Hypothesis(BaseModel):
    id: int
    text: str
    testable_claim: str


class Storyline(BaseModel):
    scqa: SCQAFramework
    governing_thought: str
    key_line: str
    hypotheses: List[Hypothesis]


class SearchResult(BaseModel):
    source: str
    url: str
    snippet: str
    date: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)


class HypothesisEvidence(BaseModel):
    hypothesis_id: int
    evidence: List[SearchResult]
    supports: bool
    confidence: Literal["low", "medium", "high"]
    conclusion: str


class ResearchResults(BaseModel):
    hypotheses_evidence: List[HypothesisEvidence]
    total_sources: int


class QualityScore(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    slide_logic: int = Field(ge=0, le=100)
    mece_structure: int = Field(ge=0, le=100)
    so_what: int = Field(ge=0, le=100)
    data_quality: int = Field(ge=0, le=100)
    chart_accuracy: int = Field(ge=0, le=100)
    visual_consistency: int = Field(ge=0, le=100)
    suggestions: List[str]
    iterations_run: Optional[int] = None
    final_report: Optional["SlideQualityReport"] = None


class JobSummary(BaseModel):
    job_id: str
    topic: str
    length: str
    status: Literal["queued", "storyline", "researching", "slides", "quality", "refining", "completed", "failed"]
    progress: int
    quality_score_overall: Optional[int] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobSummary]
    total: int
    page: int
    per_page: int


class TemplateInfo(BaseModel):
    id: str
    name: str
    filename: str
    created_at: str


class TemplateListResponse(BaseModel):
    templates: List[TemplateInfo]


class PresentationResult(BaseModel):
    job_id: str
    topic: str
    storyline: Storyline
    research: ResearchResults
    quality_score: QualityScore
    pptx_path: str
    created_at: datetime
