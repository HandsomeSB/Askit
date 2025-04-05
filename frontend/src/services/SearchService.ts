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
  private sessionId: string | null;

  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
    this.sessionId = null;

    // Try to load session from localStorage
    if (typeof window !== 'undefined') {
      this.sessionId = localStorage.getItem('sessionId');
    }
  }

  /**
   * Set session ID for authenticated requests
   */
  setSessionId(sessionId: string) {
    this.sessionId = sessionId;
    if (typeof window !== 'undefined') {
      localStorage.setItem('sessionId', sessionId);
    }
  }

  /**
   * Clear session
   */
  clearSession() {
    this.sessionId = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('sessionId');
    }
  }

  /**
   * Make authenticated API request
   */
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (this.sessionId) {
      headers.Authorization = `Bearer ${this.sessionId}`;
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
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
    const result = await this.request<SessionResponse>('/auth/google-callback', {
      method: 'POST',
      body: JSON.stringify({ code, state }),
    });
    
    if (result.sessionId) {
      this.setSessionId(result.sessionId);
    }
    
    return result;
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
    if (!this.sessionId) {
      return { valid: false };
    }
    
    try {
      const result = await this.request<VerifySessionResponse>('/verify-session');
      return { valid: true, ...result };
    } catch (error: any) {
      if (error.status === 401) {
        this.clearSession();
      }
      return { valid: false };
    }
  }
}

// Hook for using the SearchService in components
export function useSearchService() {
  const [service] = useState(() => new SearchService());
  
  return service;
}

export default SearchService;