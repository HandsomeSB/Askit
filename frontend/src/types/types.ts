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
  
  export interface SearchResponse {
    answer: string;
    sources: Array<{
      file: FileResult;
      content: string;
      relevance_score?: number;
    }>;
  }
  
  export interface ProcessFolderResponse {
    status: string;
    message: string;
    folder_id: string;
    index_id: string;
  }
  
  export interface QueryRequest {
    query: string;
    folder_id?: string;
  }
  
  export interface User {
    id: string;
    name: string;
    email: string;
    photoUrl?: string;
  }
  
  export interface SessionResponse {
    session_id: string;
    success: boolean;
    user?: User;
    expiresAt?: string;
  }
  
  export interface AuthUrlResponse {
    auth_url: string;
    state: string;
  }
  
  export interface VerifySessionResponse {
    authenticated: boolean;
    session_id?: string;
    expires?: string;
    reason?: string;
    error?: string;
  }

  export interface FileStructureResponse {
    folder_id: string;
    folder_details: any;
    contents: FileResult[];
  }