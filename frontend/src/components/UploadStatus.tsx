'use client';

import type { UploadingFile } from '@/types';

interface UploadStatusProps {
  file: UploadingFile;
}

const STATUS_ICONS: Record<string, string> = {
  pending: '⏳',
  uploading: '📤',
  parsing: '🔍',
  classifying: '🏷️',
  indexing: '📚',
  indexed: '✅',
  error: '❌',
};

export default function UploadStatus({ file }: UploadStatusProps) {
  const icon = STATUS_ICONS[file.status] || '📄';

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
