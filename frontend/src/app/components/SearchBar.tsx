'use client';

import { useState, useEffect } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface SearchBarProps {
  initialQuery?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export default function SearchBar({ initialQuery = '', onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);

  // Update local state if initialQuery changes
  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query);
    }
  };

  return (
    <div className="mb-6">
      <form onSubmit={handleSubmit} className="w-full">
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try 'passport photo', 'budget spreadsheet from last month'"
            className="w-full h-16 px-6 pr-24 text-lg rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`absolute right-2 h-12 px-6 rounded-full text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-base font-medium ${
              isLoading 
                ? 'bg-blue-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center">
                <LoadingSpinner size="sm" color="white" className="-ml-1 mr-2" />
                Searching...
              </div>
            ) : (
              'Search'
            )}
          </button>
        </div>
      </form>
      {/* <div className="mt-2 text-sm text-gray-500 px-2">
        <p>Try natural language queries like "meeting notes from last week" or "diagram about authentication flow"</p>
      </div> */}
    </div>
  );
}