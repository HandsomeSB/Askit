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
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

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
      await folderMetaManager.fetchFolderMeta();

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

  const toggleFolderExpand = (folderId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
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
        await folderMetaManager.refreshFolderMeta();
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

  // Recursive function to render folders and their children
  const renderFolder = (folder: Folder) => {
    const isExpanded = expandedFolders.has(folder.id);
    const hasChildren = folder.children && folder.children.length > 0;
    
    return (
      <div key={folder.id} className="folder-item">
        <div 
          className={`flex items-center justify-between p-2 rounded ${
            selectedFolder === folder.id ? 'bg-blue-50' : 'hover:bg-gray-50'
          }`}
        >
          <div className="flex-1 flex items-center">
            {hasChildren && (
              <button
                onClick={(event) => toggleFolderExpand(folder.id, event)}
                className="mr-2 w-5 h-5 flex items-center justify-center text-gray-500 hover:text-gray-700"
              >
                {isExpanded ? '▼' : '►'}
              </button>
            )}
            <button
              onClick={() => handleFolderSelect(folder.id)}
              className="flex-1 text-left px-2 py-1"
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
        
        {/* Render children if expanded */}
        {isExpanded && hasChildren && (
          <div className="ml-6 border-l border-gray-200 pl-2 mt-1">
            {folder.children?.map((childFolder) => (
              renderFolder(childFolder)
            ))}
          </div>
        )}
      </div>
    );
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
          folders.map((folder) => renderFolder(folder))
        )}
      </div>
    </div>
  );
}