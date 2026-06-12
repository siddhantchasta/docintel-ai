// ──────────────────────────────────────────────
// DocIntel AI — TypeScript Type Definitions
// ──────────────────────────────────────────────

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  snippet: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface ClassificationResult {
  document_type: string;
  topic: string;
  content_characteristics: string[];
  sensitivity_level: string;
  language: string;
  summary: string;
  key_entities: string[];
}

export interface DocumentInfo {
  id: string;
  filename: string;
  status: string;
  classification: ClassificationResult | null;
  page_count: number;
  uploaded_at: string;
}

export type UploadFileStatus =
  | 'pending'
  | 'uploading'
  | 'parsing'
  | 'classifying'
  | 'indexing'
  | 'indexed'
  | 'error';

export interface UploadingFile {
  file: File;
  id?: string;
  status: UploadFileStatus;
  error?: string;
  classification?: ClassificationResult;
}
