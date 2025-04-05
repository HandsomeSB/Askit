'use client';

import React from 'react';
import { SearchHistoryItem } from '../../types/types';

interface SearchHistoryProps {
  searches: SearchHistoryItem[];
  onSelectSearch: (query: string) => void;
  onClearHistory: () => void;
}

export default function SearchHistory({ 
  searches = [], 
  onSelectSearch, 
  onClearHistory 
}: SearchHistoryProps) {
  if (!searches || searches.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4 text-center">
        <p className="text-gray-500 text-sm">No recent searches</p>
      </div>
    );
  }

  // Helper to format timestamps
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    
    // Check if it's today
    if (date.toDateString() === now.toDateString()) {
      return `Today at ${date.toLocaleTimeString(undefined, { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}`;
    }
    
    // Check if it's yesterday
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday at ${date.toLocaleTimeString(undefined, { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}`;
    }
    
    // Otherwise, show date and time
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit', 
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="flex justify-between items-center p-4 border-b border-gray-100">
        <h2 className="text-lg font-medium text-gray-700">Recent Searches</h2>
        <button 
          onClick={onClearHistory}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Clear
        </button>
      </div>

      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {searches.map((search, index) => (
          <div 
            key={`${search.query}-${index}`} 
            className="p-3 hover:bg-gray-50 cursor-pointer transition-colors"
            onClick={() => onSelectSearch(search.query)}
          >
            <div className="flex items-center text-blue-600 mb-1">
              <span className="mr-2">🔍</span>
              <span className="truncate">{search.query}</span>
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>{formatTime(search.timestamp)}</span>
              <span>{search.resultCount} {search.resultCount === 1 ? 'result' : 'results'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}