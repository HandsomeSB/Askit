'use client';

import { useState } from 'react';

export default function SearchBar() {
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search functionality
    console.log('Searching for:', query);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
      <div className="text-center mb-16">
        <p className="text-2xl text-gray-700">Semantic Search on Google Drive</p>
      </div>
      
      <form onSubmit={handleSearch} className="w-1/2 max-w-xl">
        <div className="relative h-32 flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
            className="w-full h-24 px-8 text-xl rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          />
          <button
            type="submit"
            className="absolute right-4 top-1/2 transform -translate-y-1/2 h-16 px-8 bg-blue-600 text-white rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-lg"
          >
            Search
          </button>
        </div>
      </form>
    </div>
  );
} 