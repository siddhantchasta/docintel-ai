// ──────────────────────────────────────────────
// DocIntel AI — Centralized API Client
// ──────────────────────────────────────────────

import type { Citation, DocumentInfo } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'dev-api-key';

function headers(extra?: Record<string, string>): Record<string, string> {
  return {
    'X-API-Key': API_KEY,
    ...extra,
  };
}

interface UploadResponse {
  documents: { id: string; filename: string; status: string }[];
}

interface ChatResponse {
  answer: string;
  citations: Citation[];
}

interface DocumentsResponse {
  documents: DocumentInfo[];
}

/**
 * Upload one or more files via multipart/form-data.
 */
export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const res = await fetch(`${API_URL}/api/upload`, {
    method: 'POST',
    headers: headers(),
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<UploadResponse>;
}

/**
 * Poll the processing status of a single document.
 */
export async function checkStatus(documentId: string): Promise<DocumentInfo> {
  const res = await fetch(`${API_URL}/api/upload/status/${documentId}`, {
    headers: headers(),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Status check failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<DocumentInfo>;
}

/**
 * Send a chat message together with the conversation history.
 */
export async function sendMessage(
  message: string,
  conversationHistory: { role: string; content: string }[],
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: headers({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat request failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<ChatResponse>;
}

/**
 * Retrieve the list of all uploaded documents.
 */
export async function getDocuments(): Promise<DocumentsResponse> {
  const res = await fetch(`${API_URL}/api/documents`, {
    headers: headers(),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Documents fetch failed (${res.status}): ${text}`);
  }

  return res.json() as Promise<DocumentsResponse>;
}

/**
 * Build the URL for a page thumbnail image.
 * Uses query-param auth because &lt;img&gt; tags cannot send custom headers.
 */
export function getThumbnailUrl(documentId: string, pageNum: number): string {
  return `${API_URL}/api/pages/${documentId}/${pageNum}/thumbnail?api_key=${API_KEY}`;
}

/**
 * Build the URL for a full-size page image.
 * Uses query-param auth because &lt;img&gt; tags cannot send custom headers.
 */
export function getFullImageUrl(documentId: string, pageNum: number): string {
  return `${API_URL}/api/pages/${documentId}/${pageNum}/full?api_key=${API_KEY}`;
}
