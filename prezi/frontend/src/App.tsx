import { useState } from 'react';
import { TopicInput } from './components/TopicInput';
import { LoadingProgress } from './components/LoadingProgress';
import { ResultsPreview } from './components/ResultsPreview';
import { Header } from './components/Header';
import { JobHistory } from './components/JobHistory';
import { retryJob } from './services/api';

type AppState = 'input' | 'loading' | 'results' | 'history';

function App() {
  const [state, setState] = useState<AppState>('input');
  const [jobId, setJobId] = useState<string>('');

  const handleJobStart = (id: string) => {
    setJobId(id);
    setState('loading');
  };

  const handleComplete = () => {
    setState('results');
  };

  const handleRetry = async (id: string) => {
    try {
      await retryJob(id);
      setState('loading');
    } catch (err) {
      console.error('Retry failed:', err);
    }
  };

  const handleReset = () => {
    setJobId('');
    setState('input');
  };

  const handleNavigate = (view: 'input' | 'history') => {
    if (view === 'history') {
      setState('history');
    } else {
      handleReset();
    }
  };

  const handleSelectJob = (id: string, status: string) => {
    setJobId(id);
    if (status === 'completed') {
      setState('results');
    } else if (status === 'failed') {
      handleRetry(id);
    } else {
      setState('loading');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      <Header currentView={state} onNavigate={handleNavigate} />
      <div className="py-6">
        {state === 'input' && <TopicInput onJobStart={handleJobStart} />}
        {state === 'loading' && <LoadingProgress jobId={jobId} onComplete={handleComplete} onRetry={handleRetry} />}
        {state === 'results' && <ResultsPreview jobId={jobId} onReset={handleReset} />}
        {state === 'history' && <JobHistory onSelectJob={handleSelectJob} onNewPresentation={() => handleNavigate('input')} />}
      </div>
    </div>
  );
}

export default App;
