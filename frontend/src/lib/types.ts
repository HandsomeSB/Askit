// src/lib/types.ts

// Message types
export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
  isLoading?: boolean;
}

// Source document types
export interface Source {
  text: string;
  score: number;
  file_name: string;
  file_id: string;
  mime_type: string;
}

// Folder types
export interface Folder {
  id: string;
  name: string;
}

// API response types
export interface ProcessFolderResponse {
  status: string;
  message: string;
  index_id: string;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

export interface ErrorResponse {
  detail: string;
}
