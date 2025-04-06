'use client';

import { useState } from 'react';
import { 
  SessionResponse, 
  AuthUrlResponse, 
  SearchResponse, 
  VerifySessionResponse,
  ProcessFolderResponse,
  QueryRequest,
  FileStructureResponse
} from '../types/types';

class SearchService {
  private baseUrl: string;

  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Make API request with credentials
   */
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error: any = new Error(errorData.message || `Request failed with status ${response.status}`);
      error.status = response.status;
      error.data = errorData;
      
      // If unauthorized, redirect to login
      if (response.status === 401) {
        window.location.href = '/';
        throw error;
      }
      
      throw error;
    }
    
    return response.json();
  }

  /**
   * Initiate Google OAuth flow
   */
  async getGoogleAuthUrl(): Promise<AuthUrlResponse> {
    return this.request<AuthUrlResponse>('/auth/google-url');
  }

  /**
   * Handle OAuth callback
   */
  async handleOAuthCallback(code: string, state: string): Promise<SessionResponse> {
    return this.request<SessionResponse>('/auth/google-callback', {
      method: 'POST',
      body: JSON.stringify({ code, state }),
    });
  }

  /**
   * Process a Google Drive folder for indexing
   */
  async processFolder(folderId: string): Promise<ProcessFolderResponse> {
    return this.request<ProcessFolderResponse>('/process-folder-new', {
      method: 'POST',
      body: JSON.stringify({ folder_id: folderId }),
    });
  }

  /**
   * Get list of processed folders
   */
  async getFolders(): Promise<{ folders: Array<{ id: string; name: string }> }> {
    return this.request('/folders');
  }

  /**
   * Perform semantic search
   */
  async semanticSearch(query: string, folderId?: string): Promise<SearchResponse> {
    const request: QueryRequest = { query };
    if (folderId) {
      request.folder_id = folderId;
    }
    
    return this.request<SearchResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Check if session is valid
   */
  async verifySession(): Promise<VerifySessionResponse> {
    try {
      const result = await this.request<VerifySessionResponse>('/auth/check');
      return result;
    } catch (error: any) {
      return { authenticated: false };
    }
  }

  /**
   * Logout - clear session on server
   */
  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }

  /**
   * Get file structure
   */
  async getFileStructure(): Promise<FileStructureResponse> {
    console.log("Getting file structure");
    return this.request<FileStructureResponse>('/drive/file-structure');
  }
}

// Hook for using the SearchService in components
export function useSearchService() {
  const [service] = useState(() => new SearchService());
  
  return service;
}

export default SearchService;