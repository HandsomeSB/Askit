'use client';

import { useState } from 'react';
import { 
  SessionResponse, 
  AuthUrlResponse, 
  SearchResponse, 
  VerifySessionResponse 
} from '../types/types';

class SearchService {
  private baseUrl: string;

  constructor(baseUrl = 'http://localhost:8000/api') {
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
      credentials: 'include',  // This is crucial - it sends cookies with the request
      mode: 'cors',  // Explicitly set CORS mode
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error: any = new Error(errorData.message || `Request failed with status ${response.status}`);
      error.status = response.status;
      error.data = errorData;
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
      body: JSON.stringify({ "code": code, "state": state }),
    });
  }

  /**
   * Perform semantic search
   */
  async semanticSearch(query: string): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
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
}

// Hook for using the SearchService in components
export function useSearchService() {
  const [service] = useState(() => new SearchService());
  
  return service;
}

export default SearchService;