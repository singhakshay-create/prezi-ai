import React, { useState, useEffect, useRef } from 'react';
import { getProviders, getTemplates, uploadTemplate, generatePresentation } from '../services/api';
import type { ProviderInfo, TemplateInfo } from '../types';

interface TopicInputProps {
  onJobStart: (jobId: string) => void;
}

export const TopicInput: React.FC<TopicInputProps> = ({ onJobStart }) => {
  const [topic, setTopic] = useState('');
  const [length, setLength] = useState<'short' | 'medium' | 'long'>('medium');
  const [llmProviders, setLlmProviders] = useState<ProviderInfo[]>([]);
  const [researchProviders, setResearchProviders] = useState<ProviderInfo[]>([]);
  const [selectedLlm, setSelectedLlm] = useState('');
  const [selectedResearch, setSelectedResearch] = useState('mock');
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadProviders();
    loadTemplates();
  }, []);

  const loadProviders = async () => {
    try {
      const providers = await getProviders();
      setLlmProviders(providers.llm_providers);
      setResearchProviders(providers.research_providers);

      const firstAvailable = providers.llm_providers.find(p => p.available);
      if (firstAvailable) {
        setSelectedLlm(firstAvailable.id);
      }
    } catch (err) {
      setError('Failed to load providers');
    }
  };

  const loadTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data.templates);
    } catch {
      // Templates endpoint may not be critical; default will be used
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const name = file.name.replace('.pptx', '');
    setUploading(true);
    setError('');

    try {
      const template = await uploadTemplate(file, name);
      await loadTemplates();
      setSelectedTemplate(template.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload template');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    if (!selectedLlm) {
      setError('Please select an LLM provider');
      return;
    }

    setLoading(true);

    try {
      const response = await generatePresentation({
        topic,
        length,
        llm_provider: selectedLlm,
        research_provider: selectedResearch,
        template_id: selectedTemplate === 'default' ? undefined : selectedTemplate,
      });

      onJobStart(response.job_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start generation');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-4xl font-bold text-mckinsey-blue mb-2">Prezi AI</h1>
      <p className="text-gray-600 mb-8">
        Generate consulting-quality presentations powered by AI
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Topic
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mckinsey-blue focus:border-transparent"
            rows={4}
            placeholder="e.g., Should Company X enter the Indian electric vehicle market?"
            disabled={loading}
          />
        </div>

        {/* Length Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Deck Length
          </label>
          <div className="grid grid-cols-3 gap-4">
            {(['short', 'medium', 'long'] as const).map((len) => (
              <button
                key={len}
                type="button"
                onClick={() => setLength(len)}
                disabled={loading}
                className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                  length === len
                    ? 'bg-mckinsey-blue text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {len.charAt(0).toUpperCase() + len.slice(1)}
                <div className="text-xs mt-1">
                  {len === 'short' && '1-5 slides'}
                  {len === 'medium' && '6-15 slides'}
                  {len === 'long' && '16+ slides'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Template Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Presentation Template
          </label>
          <div className="flex gap-3">
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              disabled={loading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mckinsey-blue focus:border-transparent"
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pptx"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || uploading}
              className="px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors whitespace-nowrap disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload Custom'}
            </button>
          </div>
        </div>

        {/* LLM Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            AI Model
          </label>
          <select
            value={selectedLlm}
            onChange={(e) => setSelectedLlm(e.target.value)}
            disabled={loading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mckinsey-blue focus:border-transparent"
          >
            <option value="">Select AI Model</option>
            {llmProviders.map((provider) => (
              <option
                key={provider.id}
                value={provider.id}
                disabled={!provider.available}
              >
                {provider.name} {!provider.available && '(Configure API key)'}
              </option>
            ))}
          </select>
          {selectedLlm && (
            <p className="text-xs text-gray-500 mt-1">
              {llmProviders.find(p => p.id === selectedLlm)?.description}
            </p>
          )}
        </div>

        {/* Research Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Research Source
          </label>
          <select
            value={selectedResearch}
            onChange={(e) => setSelectedResearch(e.target.value)}
            disabled={loading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mckinsey-blue focus:border-transparent"
          >
            {researchProviders.map((provider) => (
              <option
                key={provider.id}
                value={provider.id}
                disabled={!provider.available}
              >
                {provider.name} {!provider.available && '(Configure API key)'}
              </option>
            ))}
          </select>
          {selectedResearch && (
            <p className="text-xs text-gray-500 mt-1">
              {researchProviders.find(p => p.id === selectedResearch)?.description}
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !selectedLlm}
          className={`w-full py-4 rounded-lg font-semibold text-white transition-colors ${
            loading || !selectedLlm
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-mckinsey-blue hover:bg-blue-800'
          }`}
        >
          {loading ? 'Starting Generation...' : 'Generate Presentation'}
        </button>
      </form>
    </div>
  );
};
