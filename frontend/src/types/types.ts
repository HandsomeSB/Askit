// types.ts

export interface FileResult {
    id: string;
    name: string;
    mimeType: string;
    webViewLink: string;
    webContentLink?: string;
    downloadUrl?: string;
    modifiedTime: string;
    description?: string;
    matchDetails?: string;
    thumbnailLink?: string;
    owners?: Array<{
      displayName: string;
      emailAddress: string;
      photoLink?: string;
    }>;
    size?: string;
    createdTime?: string;
    shared?: boolean;
    parents?: string[];
    children?: FileResult[];
  }
  
  export interface SearchHistoryItem {
    query: string;
    timestamp: string;
    resultCount: number;
  }
  
  export interface User {
    id: string;
    name: string;
    email: string;
    photoUrl?: string;
  }
  
  export interface SearchResponse {
    results: FileResult[];
    metadata?: {
      totalResults: number;
      processingTimeMs: number;
      query: string;
    };
  }
  
  export interface SessionResponse {
    sessionId: string;
    user?: User;
    expiresAt?: string;
  }
  
  export interface AuthUrlResponse {
    auth_url: string;
  }
  
  export interface VerifySessionResponse {
    authenticated: boolean;
    session_id?: string;
    expires?: string;
  }

  export interface FileStructureResponse {
    folder_id: string;
    folder_details: any;
    contents: FileResult[];
  }