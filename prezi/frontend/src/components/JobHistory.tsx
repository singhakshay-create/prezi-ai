import React, { useEffect, useState } from 'react';
import { getJobs, retryJob } from '../services/api';
import type { JobListResponse, JobSummary } from '../types';

interface JobHistoryProps {
  onSelectJob: (jobId: string, status: string) => void;
  onNewPresentation: () => void;
}

const statusBadge = (status: string) => {
  const styles: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    queued: 'bg-gray-100 text-gray-800',
  };
  const style = styles[status] || 'bg-blue-100 text-blue-800';
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${style}`}>
      {status}
    </span>
  );
};

export const JobHistory: React.FC<JobHistoryProps> = ({ onSelectJob, onNewPresentation }) => {
  const [data, setData] = useState<JobListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const perPage = 20;

  const load = async (p: number) => {
    setLoading(true);
    try {
      const result = await getJobs(p, perPage);
      setData(result);
      setPage(p);
    } catch {
      setError('Failed to load job history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1);
  }, []);

  const handleRetry = async (e: React.MouseEvent, job: JobSummary) => {
    e.stopPropagation();
    try {
      await retryJob(job.job_id);
      onSelectJob(job.job_id, 'queued');
    } catch {
      setError('Retry failed');
    }
  };

  if (loading && !data) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <div className="animate-spin h-12 w-12 border-4 border-mckinsey-blue border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading history...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  const jobs = data?.jobs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-mckinsey-blue">Job History</h2>
          <button
            onClick={onNewPresentation}
            className="px-4 py-2 bg-mckinsey-blue hover:bg-blue-800 text-white font-semibold rounded-lg text-sm transition-colors"
          >
            New Presentation
          </button>
        </div>

        {jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No presentations yet. Create your first one!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 text-sm font-medium text-gray-500">Topic</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Length</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Status</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Score</th>
                  <th className="pb-3 text-sm font-medium text-gray-500">Created</th>
                  <th className="pb-3 text-sm font-medium text-gray-500"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr
                    key={job.job_id}
                    onClick={() => onSelectJob(job.job_id, job.status)}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="py-3 pr-4 text-sm text-gray-900 max-w-xs truncate">
                      {job.topic}
                    </td>
                    <td className="py-3 pr-4 text-sm text-gray-600 capitalize">{job.length}</td>
                    <td className="py-3 pr-4">{statusBadge(job.status)}</td>
                    <td className="py-3 pr-4 text-sm font-medium text-gray-700">
                      {job.quality_score_overall !== null ? `${job.quality_score_overall}/100` : '-'}
                    </td>
                    <td className="py-3 pr-4 text-sm text-gray-500">
                      {new Date(job.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3">
                      {job.status === 'failed' && (
                        <button
                          onClick={(e) => handleRetry(e, job)}
                          className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded text-xs font-medium transition-colors"
                        >
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <button
              onClick={() => load(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 rounded text-sm font-medium bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => load(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 rounded text-sm font-medium bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
