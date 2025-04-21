'use client';

import { useState, useEffect } from 'react';
import { useSearchService } from '../../services/SearchService';
import { FolderMetaManager, Folder} from '../models/FolderMetaManager';

export default function FolderManager({ 
  onFolderSelect,
  isAuthenticated: parentIsAuthenticated 
}: { 
  onFolderSelect: (folderId: string) => void;
  isAuthenticated: boolean;
}) {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [processingFolders, setProcessingFolders] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [folderMetaManager] = useState(() => new FolderMetaManager());

  const searchService = useSearchService();

  useEffect(() => {
    if (parentIsAuthenticated) {
      loadFolders();
    }
  }, [parentIsAuthenticated]);

  const loadFolders = async () => {
    if (!parentIsAuthenticated) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await searchService.getFolderStructure();
      // Add processed: false by default if not present
      const folders = response.map((folder) => ({
        ...folder,
        processed: false,
      }));
      folderMetaManager.setFolders(folders);

      setFolders(folderMetaManager.getFolderStructure());
    } catch (err: any) {
      setError('Failed to load folders: ' + (err.message || 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleFolderSelect = (folderId: string) => {
    setSelectedFolder(folderId);
    onFolderSelect(folderId);
  };

  const handleProcessFolder = async (folderId: string, event: React.MouseEvent) => {
    console.log("handleProcessFolder called with folderId:", folderId);
    event.stopPropagation();
    if (!parentIsAuthenticated) return;
    
    setProcessingFolders(prev => new Set(prev).add(folderId));
    setError(null);
    setProcessingStatus('Processing folder...');

    try {
      const response = await searchService.processFolder(folderId);
      setProcessingStatus(response.message);

      if (response.status === 'success') {
        folderMetaManager.updateProcessedState(folderId, true);
        setFolders(folderMetaManager.getFolderStructure());
      }

    } catch (err: any) {
      const errorMessage = err.data?.detail || err.message || 'Unknown error';
      setError(`Failed to process folder: ${errorMessage}`);
    } finally {
      setProcessingFolders(prev => {
        const newSet = new Set(prev);
        newSet.delete(folderId);
        return newSet;
      });
    }
  };

  if (!parentIsAuthenticated) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Folders</h2>
        <p className="text-gray-500 text-center py-4">
          Please log in to view and manage folders.
        </p>
      </div>
    );
  }

  // Loading animation component
  const LoadingSpinner = () => (
    <div className="flex justify-center items-center py-8">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
    </div>
  );

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
        {isLoading ? (
          <LoadingSpinner />
        ) : folders.length === 0 ? (
          <p className="text-gray-500 text-center py-4">
            No folders available. Select a folder to process.
          </p>
        ) : (
          folders.map((folder) => (
            <div 
              key={folder.id}
              className={`flex items-center justify-between p-2 rounded ${
                selectedFolder === folder.id ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex-1">
                <button
                  onClick={() => handleFolderSelect(folder.id)}
                  className="w-full text-left px-2 py-1"
                >
                  {folder.name}
                </button>
              </div>
              
              {/* Process button */}
              <div className="ml-2">
                {folder.processed ? (
                  <div className="px-3 py-1 text-green-600">
                    <span style={{ color: 'green', fontSize: '24px' }}>
                      ✓
                    </span>
                  </div>
                ) : (
                  <button
                    onClick={(event) => handleProcessFolder(folder.id, event)}
                    disabled={processingFolders.has(folder.id)}
                    className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
                  >
                    {processingFolders.has(folder.id) ? (
                      <span className="flex items-center">
                        <span className="animate-spin h-4 w-4 mr-2 border-b-2 border-blue-500 rounded-full"></span>
                        Processing...
                      </span>
                    ) : 'Process'}
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}