'use client';

import { useEffect, useCallback } from 'react';

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  documentName: string;
  pageNumber: number;
}

export default function ImageModal({
  isOpen,
  onClose,
  imageUrl,
  documentName,
  pageNumber,
}: ImageModalProps) {
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-content">
        {/* Close button */}
        <button
          className="modal-close"
          onClick={onClose}
          aria-label="Close modal"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Image */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          className="modal-image"
          src={imageUrl}
          alt={`${documentName} — Page ${pageNumber}`}
        />

        {/* Caption */}
        <div className="modal-caption">
          <strong>{documentName}</strong> — Page {pageNumber}
        </div>
      </div>
    </div>
  );
}
