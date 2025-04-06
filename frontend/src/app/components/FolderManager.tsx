'use client';

import { useState, useEffect } from 'react';
import { useSearchService } from '../../services/SearchService';

interface Folder {
  id: string;
  name: string;
}

export default function FolderManager({ onFolderSelect }: { onFolderSelect: (folderId: string) => void }) {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const searchService = useSearchService();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const { authenticated } = await searchService.verifySession();
      setIsAuthenticated(authenticated);
      if (authenticated) {
        loadFolders();
      }
    } catch (err) {
      console.error('Auth check failed:', err);
      setIsAuthenticated(false);
    }
  };

  const loadFolders = async () => {
    if (!isAuthenticated) return;
    
    try {
      const response = await searchService.getFolders();
      setFolders(response.folders);
    } catch (err: any) {
      setError('Failed to load folders: ' + (err.message || 'Unknown error'));
    }
  };

  const handleFolderSelect = (folderId: string) => {
    setSelectedFolder(folderId);
    onFolderSelect(folderId);
  };

  const handleProcessFolder = async (folderId: string) => {
    if (!isAuthenticated) return;
    
    setIsLoading(true);
    setError(null);
    setProcessingStatus('Processing folder...');

    try {
      const response = await searchService.processFolder(folderId);
      setProcessingStatus(response.message);
      
      // Reload folders to get updated list
      await loadFolders();
    } catch (err: any) {
      setError('Failed to process folder: ' + (err.message || 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Folders</h2>
        <p className="text-gray-500 text-center py-4">
          Please log in to view and manage folders.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">Folders</h2>
      
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 text-red-700">
          {error}
        </div>
      )}
      
      {processingStatus && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 text-blue-700">
          {processingStatus}
        </div>
      )}
      
      <div className="space-y-2">
        {folders.map((folder) => (
          <div 
            key={folder.id}
            className={`flex items-center justify-between p-2 rounded ${
              selectedFolder === folder.id ? 'bg-blue-50' : 'hover:bg-gray-50'
            }`}
          >
            <button
              onClick={() => handleFolderSelect(folder.id)}
              className="flex-1 text-left px-2 py-1"
            >
              {folder.name}
            </button>
            
            <button
              onClick={() => handleProcessFolder(folder.id)}
              disabled={isLoading}
              className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
            >
              {isLoading ? 'Processing...' : 'Process'}
            </button>
          </div>
        ))}
        
        {folders.length === 0 && (
          <p className="text-gray-500 text-center py-4">
            No folders available. Select a folder to process.
          </p>
        )}
      </div>
    </div>
  );
} 