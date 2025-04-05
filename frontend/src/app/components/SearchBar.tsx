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
      
      <form onSubmit={handleSearch} className="w-3/4 max-w-2xl">
        <div className="relative h-24 flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
            className="w-full h-24 px-4 text-xl rounded-lg border border-black focus:outline-none focus:ring-1 focus:ring-black focus:border-black shadow-sm placeholder-gray-400 transition-all duration-300"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 h-14 px-6 bg-black text-white rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 text-lg"
          >
            Search
          </button>
        </div>
      </form>
    </div>
  );
} 