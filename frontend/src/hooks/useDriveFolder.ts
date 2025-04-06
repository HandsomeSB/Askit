import { useState, useCallback } from 'react';
import { useSearchService } from '../services/SearchService';

interface Folder {
  id: string;
  name: string;
  children?: Folder[];
}

export function useDriveFolder() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const searchService = useSearchService();

  const connectToDrive = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await searchService.request<Folder[]>('/drive/folder-structure');
      setFolders(response);
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to fetch folders:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [searchService]);

  return {
    folders,
    isLoading,
    isConnected,
    connectToDrive
  };
} 