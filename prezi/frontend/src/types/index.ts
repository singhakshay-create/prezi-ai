export interface ProviderInfo {
  id: string;
  name: string;
  available: boolean;
  description: string;
}

export interface ProvidersResponse {
  llm_providers: ProviderInfo[];
  research_providers: ProviderInfo[];
}

export interface GenerateRequest {
  topic: string;
  length: 'short' | 'medium' | 'long';
  llm_provider: string;
  research_provider: string;
  template_id?: string;
}

export interface TemplateInfo {
  id: string;
  name: string;
  filename: string;
  created_at: string;
}

export interface TemplateListResponse {
  templates: TemplateInfo[];
}

export interface GenerateResponse {
  job_id: string;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'storyline' | 'researching' | 'slides' | 'quality' | 'completed' | 'failed';
  progress: number;
  message: string;
  error?: string;
}

export interface JobSummary {
  job_id: string;
  topic: string;
  length: string;
  status: 'queued' | 'storyline' | 'researching' | 'slides' | 'quality' | 'completed' | 'failed';
  progress: number;
  quality_score_overall: number | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface JobListResponse {
  jobs: JobSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface QualityScore {
  overall_score: number;
  slide_logic: number;
  mece_structure: number;
  so_what: number;
  data_quality: number;
  chart_accuracy: number;
  visual_consistency: number;
  suggestions: string[];
}

export interface JobResult {
  job_id: string;
  topic: string;
  length: string;
  storyline: any;
  research: any;
  quality_score: QualityScore;
  created_at: string;
  completed_at: string;
}
