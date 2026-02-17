import React from 'react';

interface HeaderProps {
  currentView: string;
  onNavigate: (view: 'input' | 'history') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView, onNavigate }) => {
  const isHistory = currentView === 'history';
  const isNew = !isHistory;

  return (
    <header className="bg-white shadow-sm mb-8">
      <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-mckinsey-blue">Prezi AI</h1>
        <nav className="flex gap-2">
          <button
            onClick={() => onNavigate('input')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isNew
                ? 'bg-mckinsey-blue text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            New
          </button>
          <button
            onClick={() => onNavigate('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isHistory
                ? 'bg-mckinsey-blue text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            History
          </button>
        </nav>
      </div>
    </header>
  );
};
