import axios from 'axios';
import type { ProvidersResponse, GenerateRequest, GenerateResponse, JobStatus, JobResult, JobListResponse, TemplateListResponse, TemplateInfo } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getProviders = async (): Promise<ProvidersResponse> => {
  const response = await api.get<ProvidersResponse>('/providers');
  return response.data;
};

export const generatePresentation = async (request: GenerateRequest): Promise<GenerateResponse> => {
  const response = await api.post<GenerateResponse>('/generate', request);
  return response.data;
};

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get<JobStatus>(`/status/${jobId}`);
  return response.data;
};

export const getJobResult = async (jobId: string): Promise<JobResult> => {
  const response = await api.get<JobResult>(`/result/${jobId}`);
  return response.data;
};

export const getJobs = async (page: number = 1, perPage: number = 20): Promise<JobListResponse> => {
  const response = await api.get<JobListResponse>('/jobs', { params: { page, per_page: perPage } });
  return response.data;
};

export const retryJob = async (jobId: string): Promise<GenerateResponse> => {
  const response = await api.post<GenerateResponse>(`/retry/${jobId}`);
  return response.data;
};

export const downloadPresentation = (jobId: string): string => {
  return `${API_BASE_URL}/api/download/${jobId}`;
};

export const downloadPdf = (jobId: string): string => {
  return `${API_BASE_URL}/api/download/${jobId}/pdf`;
};

export const getWebSocketUrl = (jobId: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = new URL(API_BASE_URL);
  return `${protocol}//${url.host}/ws/progress/${jobId}`;
};

export const getTemplates = async (): Promise<TemplateListResponse> => {
  const response = await api.get<TemplateListResponse>('/templates');
  return response.data;
};

export const uploadTemplate = async (file: File, name: string): Promise<TemplateInfo> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  const response = await api.post<TemplateInfo>('/templates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const deleteTemplate = async (templateId: string): Promise<void> => {
  await api.delete(`/templates/${templateId}`);
};
