export interface Document {
  id: number;
  filename: string;
  created_at: string;
  chunk_count: number;
}

export interface SearchResult {
  chunk_id: number;
  document_id: number;
  filename: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: SearchResult[];
}

export interface DeleteDocumentResponse {
  message: string;
  document_id: number;
}

export interface ProjectAnalysis {
  project_summary: string;
  key_dates: string[];
  budget_information: string[];
  risks: string[];
  open_tasks: string[];
  stakeholders: string[];
  source_documents: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SearchResult[];
}
