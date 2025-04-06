'use client';

import React from 'react';
import { FileResult } from '../../types/types';
import FileIcon from './FileIcon';
import LoadingSpinner from './LoadingSpinner';

interface ResultsListProps {
  results: FileResult[];
  isLoading: boolean;
  answer?: string;
}

export default function ResultsList({ results, isLoading, answer }: ResultsListProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8 text-center">
        <div className="flex justify-center mb-4">
          <LoadingSpinner size="lg" color="blue" />
        </div>
        <p className="text-gray-600">Searching your Google Drive with semantic understanding...</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8 text-center">
        <p className="text-gray-500">No results found. Try a search above.</p>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {answer && (
        <div className="p-4 border-b border-gray-100 bg-blue-50">
          <h2 className="text-lg font-medium text-blue-800 mb-2">Answer</h2>
          <p className="text-blue-700">{answer}</p>
        </div>
      )}
      
      <h2 className="text-lg font-medium p-4 border-b border-gray-100">Search Results</h2>
      <div className="divide-y divide-gray-100">
        {results.map((result) => (
          <div key={result.id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex">
              <div className="mr-4 flex-shrink-0">
                <FileIcon mimeType={result.mimeType} size="md" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-blue-600 mb-1 truncate">
                  <a href={result.webViewLink} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {result.name}
                  </a>
                </h3>
                <div className="flex text-sm text-gray-500 mb-2 flex-wrap gap-x-4">
                  <span>{result.mimeType.split('.').pop()?.toUpperCase()}</span>
                  <span>Modified: {formatDate(result.modifiedTime)}</span>
                </div>
                {result.description && (
                  <p className="text-gray-700 mb-2 text-sm">{result.description}</p>
                )}
                {result.matchDetails && (
                  <div className="bg-blue-50 p-2 rounded-md mb-3 text-sm">
                    <p className="text-blue-800">
                      <span className="font-medium">Matched Content:</span> {result.matchDetails}
                    </p>
                  </div>
                )}
                <div className="flex gap-2 mt-2">
                  <a 
                    href={result.webViewLink} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    View
                  </a>
                  {(result.downloadUrl || result.webContentLink) && (
                    <a 
                      href={result.downloadUrl || result.webContentLink} 
                      className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                      download
                    >
                      Download
                    </a>
                  )}
                </div>
              </div>
              {result.thumbnailLink && (
                <div className="ml-4 flex-shrink-0 w-20 h-20 rounded-md overflow-hidden border border-gray-200">
                  <img 
                    src={result.thumbnailLink} 
                    alt={`Thumbnail for ${result.name}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}