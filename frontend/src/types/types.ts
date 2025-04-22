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
      text: string;
      metadata: {
        id?: string;
        modified_time?: string;
        [key: string]: any;
      };
      score?: number;
      file_name: string;
      mime_type: string;
      web_view_link: string;
    }>;
  }
  
  export interface ProcessFolderResponse {
    status: string;
    message: string;
    index_id: string;
    failed_files?: string[];
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

  export interface FolderStructureResponse {
    id: string; 
    name: string; 
    modifiedTime: string;
    children: FolderStructureResponse[]
  }

  export interface IndexMetaResponse {
    folder_id: string;
    absolute_id_path: string;
    time_indexed: string;
    children: IndexMetaResponse[];
  }