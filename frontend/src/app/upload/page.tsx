'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { UploadingFile, DocumentInfo } from '@/types';
import { uploadFiles, checkStatus, getDocuments } from '@/lib/api';
import FileUploader from '@/components/FileUploader';
import UploadStatus from '@/components/UploadStatus';

export default function UploadPage() {
  const [files, setFiles] = useState<UploadingFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [existingDocs, setExistingDocs] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch existing documents
  useEffect(() => {
    getDocuments()
      .then((res) => setExistingDocs(res.documents))
      .catch(() => {
        /* silently handle — backend might not be running */
      })
      .finally(() => setLoadingDocs(false));
  }, []);

  // Polling for files that are not yet done
  const pollStatuses = useCallback(() => {
    setFiles((prev) => {
      const needsPolling = prev.filter(
        (f) =>
          f.id &&
          f.status !== 'indexed' &&
          f.status !== 'error' &&
          f.status !== 'pending',
      );

      if (needsPolling.length === 0) {
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        return prev;
      }

      // Fire status checks (async, updates state in then-callbacks)
      needsPolling.forEach((f) => {
        if (!f.id) return;
        checkStatus(f.id)
          .then((info) => {
            setFiles((current) =>
              current.map((cf) =>
                cf.id === info.id
                  ? {
                      ...cf,
                      status: info.status as UploadingFile['status'],
                      classification: info.classification ?? undefined,
                      error: undefined,
                    }
                  : cf,
              ),
            );
          })
          .catch((err) => {
            setFiles((current) =>
              current.map((cf) =>
                cf.id === f.id
                  ? {
                      ...cf,
                      status: 'error' as const,
                      error: err instanceof Error ? err.message : 'Status check failed',
                    }
                  : cf,
              ),
            );
          });
      });

      return prev;
    });
  }, []);

  // Start polling whenever there are active uploads
  useEffect(() => {
    const hasActive = files.some(
      (f) =>
        f.id &&
        f.status !== 'indexed' &&
        f.status !== 'error' &&
        f.status !== 'pending',
    );

    if (hasActive && !pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(pollStatuses, 2000);
    }

    if (!hasActive && pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [files, pollStatuses]);

  function handleFilesSelected(selectedFiles: File[]) {
    const newEntries: UploadingFile[] = selectedFiles.map((file) => ({
      file,
      status: 'pending' as const,
    }));
    setFiles((prev) => [...newEntries, ...prev]);
  }

  async function handleUpload() {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    setUploading(true);

    // Mark all pending as uploading
    setFiles((prev) =>
      prev.map((f) =>
        f.status === 'pending' ? { ...f, status: 'uploading' as const } : f,
      ),
    );

    try {
      const rawFiles = pendingFiles.map((f) => f.file);
      const response = await uploadFiles(rawFiles);

      // Map returned IDs back to our file entries
      setFiles((prev) => {
        const updated = [...prev];
        response.documents.forEach((doc) => {
          const idx = updated.findIndex(
            (f) =>
              f.file.name === doc.filename &&
              (f.status === 'uploading' || f.status === 'pending'),
          );
          if (idx !== -1) {
            updated[idx] = {
              ...updated[idx],
              id: doc.id,
              status: (doc.status as UploadingFile['status']) || 'uploading',
            };
          }
        });
        return updated;
      });
    } catch (err) {
      // Mark all uploading as error
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'uploading'
            ? {
                ...f,
                status: 'error' as const,
                error: err instanceof Error ? err.message : 'Upload failed',
              }
            : f,
        ),
      );
    } finally {
      setUploading(false);
    }
  }

  function handleRemovePending(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  const pendingCount = files.filter((f) => f.status === 'pending').length;
  const activeFiles = files.filter((f) => f.status !== 'pending');

  return (
    <div className="upload-page">
      {/* Header */}
      <div className="upload-header animate-fade-in-up">
        <h1>Upload Documents</h1>
        <p>
          Drag &amp; drop your PDFs and images below. The platform will automatically
          parse, classify, and index each document.
        </p>
      </div>

      {/* File Uploader */}
      <FileUploader
        onFilesSelected={handleFilesSelected}
        disabled={uploading}
      />

      {/* Pending files list */}
      {pendingCount > 0 && (
        <div className="selected-files animate-fade-in-up">
          {files.map((f, i) =>
            f.status === 'pending' ? (
              <div key={`pending-${i}`} className="selected-file-item">
                <div className="selected-file-info">
                  <span className="selected-file-icon">
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </span>
                  <div>
                    <div className="selected-file-name">{f.file.name}</div>
                    <div className="selected-file-size">
                      {(f.file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                </div>
                <button
                  className="selected-file-remove"
                  onClick={() => handleRemovePending(i)}
                  aria-label="Remove file"
                >
                  ✕
                </button>
              </div>
            ) : null,
          )}

          <div className="upload-actions">
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? (
                <>
                  <span className="spinner" /> Uploading…
                </>
              ) : (
                <>
                  Upload {pendingCount} file{pendingCount > 1 ? 's' : ''}
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Active upload statuses */}
      {activeFiles.length > 0 && (
        <div className="upload-status-list">
          <div className="section-divider">Processing queue</div>
          {activeFiles.map((f, i) => (
            <UploadStatus key={f.id || `active-${i}`} file={f} />
          ))}
        </div>
      )}

      {/* Previously uploaded documents */}
      {!loadingDocs && existingDocs.length > 0 && (
        <div className="documents-section">
          <div className="section-divider">Document repository</div>
          <div className="documents-table-container">
            <table className="documents-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Status</th>
                  <th>Pages</th>
                  <th>Type</th>
                  <th>Topic</th>
                </tr>
              </thead>
              <tbody>
                {existingDocs.map((doc) => (
                  <tr key={doc.id}>
                    <td className="doc-name-cell">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.0"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        style={{ color: 'var(--text-secondary)' }}
                      >
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      <span className="doc-name-text" title={doc.filename}>{doc.filename}</span>
                    </td>
                    <td>
                      <span className={`status-badge status-${doc.status}`}>
                        <span className="status-dot" />
                        {doc.status}
                      </span>
                    </td>
                    <td>{doc.page_count > 0 ? `${doc.page_count} pages` : '—'}</td>
                    <td>{doc.classification?.document_type || '—'}</td>
                    <td>{doc.classification?.topic || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {loadingDocs && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      )}
    </div>
  );
}
