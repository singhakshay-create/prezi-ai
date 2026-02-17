import React, { useEffect, useState, useRef, useCallback } from 'react';
import { getJobStatus, getWebSocketUrl } from '../services/api';
import type { JobStatus } from '../types';

interface LoadingProgressProps {
  jobId: string;
  onComplete: () => void;
  onRetry?: (jobId: string) => void;
}

export const LoadingProgress: React.FC<LoadingProgressProps> = ({ jobId, onComplete, onRetry }) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const handleStatusUpdate = useCallback((jobStatus: JobStatus) => {
    setStatus(jobStatus);
    if (jobStatus.status === 'completed') {
      onCompleteRef.current();
    } else if (jobStatus.status === 'failed') {
      setError(jobStatus.error || 'Generation failed');
    }
  }, []);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return;
    const poll = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        handleStatusUpdate(jobStatus);
      } catch {
        setError('Failed to fetch status');
      }
    };
    intervalRef.current = setInterval(poll, 2000);
  }, [jobId, handleStatusUpdate]);

  useEffect(() => {
    // Initial HTTP poll for immediate state
    const initialPoll = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        handleStatusUpdate(jobStatus);
      } catch {
        // Will be handled by WS or polling
      }
    };
    initialPoll();

    // Try WebSocket first
    try {
      const ws = new WebSocket(getWebSocketUrl(jobId));
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as JobStatus;
          handleStatusUpdate(data);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onerror = () => {
        // Fall back to polling
        startPolling();
      };

      ws.onclose = () => {
        // Fall back to polling if WS closes unexpectedly
        startPolling();
      };
    } catch {
      // WebSocket not available, use polling
      startPolling();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, handleStatusUpdate, startPolling]);

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800 mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
          {onRetry && (
            <button
              onClick={() => onRetry(jobId)}
              className="mt-4 px-6 py-2 bg-mckinsey-blue hover:bg-blue-800 text-white font-semibold rounded-lg transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-center">
        <div className="animate-spin h-12 w-12 border-4 border-mckinsey-blue border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    );
  }

  const statusMessages = {
    queued: 'Queued for processing...',
    storyline: 'Generating storyline with SCQA framework...',
    researching: 'Researching hypotheses...',
    slides: 'Creating presentation slides...',
    quality: 'Running quality check...',
    completed: 'Completed!',
    failed: 'Failed'
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-bold text-mckinsey-blue mb-6">
          Generating Your Presentation
        </h2>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{statusMessages[status.status]}</span>
            <span>{status.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-mckinsey-blue h-3 rounded-full transition-all duration-500"
              style={{ width: `${status.progress}%` }}
            ></div>
          </div>
        </div>

        {/* Status Message */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-700">{status.message}</p>
        </div>

        {/* Steps Indicator */}
        <div className="mt-8 grid grid-cols-5 gap-2">
          {['Storyline', 'Research', 'Slides', 'Quality', 'Done'].map((step, idx) => {
            const stepStatus = ['storyline', 'researching', 'slides', 'quality', 'completed'];
            const currentIdx = stepStatus.indexOf(status.status);
            const isActive = idx <= currentIdx;

            return (
              <div key={step} className="text-center">
                <div
                  className={`w-10 h-10 mx-auto rounded-full flex items-center justify-center mb-2 ${
                    isActive ? 'bg-mckinsey-blue text-white' : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {idx < currentIdx ? '✓' : idx + 1}
                </div>
                <div className={`text-xs ${isActive ? 'text-mckinsey-blue font-medium' : 'text-gray-500'}`}>
                  {step}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
