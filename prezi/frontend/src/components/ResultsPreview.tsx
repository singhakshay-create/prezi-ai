import React, { useEffect, useState } from 'react';
import { getJobResult, downloadPresentation, downloadPdf } from '../services/api';
import type { JobResult } from '../types';

interface ResultsPreviewProps {
  jobId: string;
  onReset: () => void;
}

export const ResultsPreview: React.FC<ResultsPreviewProps> = ({ jobId, onReset }) => {
  const [result, setResult] = useState<JobResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadResult();
  }, [jobId]);

  const loadResult = async () => {
    try {
      const data = await getJobResult(jobId);
      setResult(data);
    } catch (err) {
      setError('Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-center">
        <div className="animate-spin h-12 w-12 border-4 border-mckinsey-blue border-t-transparent rounded-full mx-auto"></div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error || 'No results available'}</p>
        </div>
      </div>
    );
  }

  const qualityScore = result.quality_score;
  const scoreColor = qualityScore.overall_score >= 80 ? 'text-green-600' :
                      qualityScore.overall_score >= 70 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-mckinsey-blue">
            Presentation Complete!
          </h2>
          <div className="text-right">
            <div className={`text-5xl font-bold ${scoreColor}`}>
              {qualityScore.overall_score}
            </div>
            <div className="text-sm text-gray-600">Quality Score</div>
          </div>
        </div>

        {/* Topic */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-2">Topic</h3>
          <p className="text-gray-900">{result.topic}</p>
        </div>

        {/* Storyline Preview */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-mckinsey-blue mb-3">Storyline</h3>
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded">
              <span className="font-medium text-gray-700">Situation: </span>
              <span className="text-gray-900">{result.storyline.scqa.situation.substring(0, 150)}...</span>
            </div>
            <div className="p-3 bg-blue-50 rounded">
              <span className="font-medium text-gray-700">Answer: </span>
              <span className="text-gray-900">{result.storyline.scqa.answer.substring(0, 150)}...</span>
            </div>
          </div>
        </div>

        {/* Quality Breakdown */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-mckinsey-blue mb-3">Quality Breakdown</h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Slide Logic', score: qualityScore.slide_logic },
              { label: 'MECE Structure', score: qualityScore.mece_structure },
              { label: 'So What', score: qualityScore.so_what },
              { label: 'Data Quality', score: qualityScore.data_quality },
              { label: 'Chart Accuracy', score: qualityScore.chart_accuracy },
              { label: 'Visual Consistency', score: qualityScore.visual_consistency },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">{item.label}</span>
                <span className="font-semibold text-mckinsey-blue">{item.score}/100</span>
              </div>
            ))}
          </div>
        </div>

        {/* Suggestions */}
        {qualityScore.suggestions.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-mckinsey-blue mb-3">Suggestions</h3>
            <ul className="space-y-2">
              {qualityScore.suggestions.map((suggestion, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-light-blue mr-2">•</span>
                  <span className="text-gray-700">{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Research Stats */}
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-2">Research Summary</h3>
          <p className="text-gray-900">
            Validated {result.storyline.hypotheses.length} hypotheses using {result.research.total_sources} sources
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <a
            href={downloadPresentation(jobId)}
            className="flex-1 py-4 bg-mckinsey-blue hover:bg-blue-800 text-white font-semibold rounded-lg text-center transition-colors"
            download
          >
            Download PPTX
          </a>
          <a
            href={downloadPdf(jobId)}
            className="flex-1 py-4 bg-light-blue hover:bg-blue-500 text-white font-semibold rounded-lg text-center transition-colors"
            download
          >
            Download PDF
          </a>
          <button
            onClick={onReset}
            className="flex-1 py-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg transition-colors"
          >
            Create Another
          </button>
        </div>
      </div>
    </div>
  );
};
