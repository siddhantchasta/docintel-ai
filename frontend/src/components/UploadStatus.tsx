'use client';

import type { UploadingFile } from '@/types';
import { type ReactNode } from 'react';

interface UploadStatusProps {
  file: UploadingFile;
}

function getStatusIcon(status: UploadingFile['status']): ReactNode {
  switch (status) {
    case 'pending':
      return (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: 'var(--text-muted)' }}
        >
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      );
    case 'indexed':
      return (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: 'var(--status-indexed-dot)' }}
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case 'error':
      return (
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: 'var(--status-error-dot)' }}
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      );
    default:
      // Active processing states (uploading, parsing, classifying, indexing)
      return <span className="spinner" style={{ display: 'inline-block' }} />;
  }
}

export default function UploadStatus({ file }: UploadStatusProps) {
  const icon = getStatusIcon(file.status);

  return (
    <div className="upload-status-card">
      <div className="upload-status-icon">{icon}</div>

      <div className="upload-status-details">
        {/* Filename */}
        <div className="upload-status-filename">{file.file.name}</div>

        {/* Status badge */}
        <div>
          <span className={`status-badge status-${file.status}`}>
            <span className="status-dot" />
            {file.status}
          </span>
        </div>

        {/* Error message */}
        {file.status === 'error' && file.error && (
          <div className="upload-status-error">{file.error}</div>
        )}

        {/* Classification summary */}
        {file.status === 'indexed' && file.classification && (
          <div className="classification-summary">
            <div className="classification-item">
              <span className="classification-label">Type</span>
              <span className="classification-value">
                {file.classification.document_type}
              </span>
            </div>
            <div className="classification-item">
              <span className="classification-label">Topic</span>
              <span className="classification-value">
                {file.classification.topic}
              </span>
            </div>
            <div className="classification-item">
              <span className="classification-label">Sensitivity</span>
              <span className="classification-value">
                {file.classification.sensitivity_level}
              </span>
            </div>
            {file.classification.summary && (
              <div
                className="classification-item"
                style={{ gridColumn: '1 / -1' }}
              >
                <span className="classification-label">Summary</span>
                <span className="classification-value">
                  {file.classification.summary}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
