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
          ✕
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
