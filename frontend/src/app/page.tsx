'use client';

import { useState, useEffect } from 'react';
import Logo from './components/Logo';
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList'
import LoginButton from './components/LoginButton';
import SearchHistory from './components/SearchHistory';
import { useSearchService } from '../services/SearchService';

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  
  const searchService = useSearchService();

  // Check if user is already authenticated and load search history
  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log("Checking auth");
        // Verify any existing session
        const { authenticated } = await searchService.verifySession();
        setIsAuthenticated(authenticated);
        console.log("Authenticated:", authenticated);
        
        if (authenticated) {
          // Load search history from localStorage
          const savedHistory = localStorage.getItem('searchHistory');
          if (savedHistory) {
            try {
              setSearchHistory(JSON.parse(savedHistory));
            } catch (e) {
              console.error('Error parsing search history:', e);
              localStorage.removeItem('searchHistory');
            }
          }
        }
        
        // This is being moved to the callback page TO DELETE
        // Handle OAuth callback if present in URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (code && state) {
          setIsLoading(true);
          await handleOAuthCallback(code, state);
        }

        // Testing
        try {
          console.log("Getting file structure");
          const fileStructure = await searchService.getFileStructure();
          console.log("File structure:", fileStructure);
        } catch (error) {
          console.error("Error getting file structure:", error);
        }

      } catch (err) {
        console.error('Auth check failed:', err);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const handleLogin = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { auth_url } = await searchService.getGoogleAuthUrl();

      window.location.href = auth_url;
    } catch (err) {
      console.error('Error during login:', err);
      setError('Failed to initiate login process');
      setIsLoading(false);
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { sessionId } = await searchService.handleOAuthCallback(code, state);
      setIsAuthenticated(true);
      
      // Clean URL
      window.history.replaceState({}, document.title, '/');
    } catch (err) {
      console.error('Error processing OAuth callback:', err);
      setError('Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    setCurrentQuery(query);
    setIsLoading(true);
    setError(null);
    
    try {
      const { results } = await searchService.semanticSearch(query);
      setSearchResults(results || []);
      
      // Add to search history
      const newSearchItem = {
        query,
        timestamp: new Date().toISOString(),
        resultCount: results?.length || 0
      };
      
      const updatedHistory = [
        newSearchItem,
        ...searchHistory.filter(item => item.query !== query).slice(0, 9)
      ];
      
      setSearchHistory(updatedHistory);
      localStorage.setItem('searchHistory', JSON.stringify(updatedHistory));
      
    } catch (err: any) {
      console.error('Error during search:', err);
      
      if (err.status === 401) {
        setError('Your session has expired. Please log in again.');
        setIsAuthenticated(false);
      } else {
        setError('Search failed: ' + (err.message || 'Unknown error'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistory = (query: string) => {
    setCurrentQuery(query);
    handleSearch(query);
  };

  const handleClearHistory = () => {
    setSearchHistory([]);
    localStorage.removeItem('searchHistory');
  };

  const handleLogout = () => {
    searchService.logout();
    setIsAuthenticated(false);
    setSearchResults([]);
    setSearchHistory([]);
  };

  return (
    <main className="min-h-screen flex flex-col p-4 bg-gradient-to-b from-white to-gray-50">
      <header className="flex justify-between items-center mb-8">
        <Logo />
        {isAuthenticated && (
          <button 
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-full hover:bg-gray-100 transition-colors"
          >
            Sign Out
          </button>
        )}
      </header>

      {!isAuthenticated ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold text-gray-800 mb-4">Semantic Search for Google Drive</h1>
            <p className="text-lg text-gray-600 mb-8">
              Find what you're looking for, even when you don't know the exact name
            </p>
            <LoginButton onClick={handleLogin} isLoading={isLoading} />
          </div>
        </div>
      ) : (
        <div className="flex-1 max-w-5xl mx-auto w-full">
          <SearchBar 
            initialQuery={currentQuery} 
            onSearch={handleSearch} 
            isLoading={isLoading} 
          />
          
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-red-700">
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <SearchHistory 
                searches={searchHistory}
                onSelectSearch={handleSelectHistory}
                onClearHistory={handleClearHistory}
              />
            </div>
            
            <div className="lg:col-span-2">
              <ResultsList 
                results={searchResults} 
                isLoading={isLoading} 
              />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}