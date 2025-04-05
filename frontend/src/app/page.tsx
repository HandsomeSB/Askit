'use client';

import { useState } from 'react';
import Logo from './components/Logo';
import SearchBar from './components/SearchBar';

export default function Home() {
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search functionality
    console.log('Searching for:', query);
  };

  return (
    <main className="min-h-screen flex flex-col p-4 bg-gradient-to-b from-white to-gray-50">
      <Logo />
      <SearchBar />
    </main>
  );
}
