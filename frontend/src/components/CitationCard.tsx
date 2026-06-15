'use client';

import type { Citation } from '@/types';
import { getThumbnailUrl } from '@/lib/api';

interface CitationCardProps {
  citation: Citation;
  onImageClick: (documentId: string, pageNumber: number) => void;
}

export default function CitationCard({ citation, onImageClick }: CitationCardProps) {
  const thumbnailSrc = getThumbnailUrl(citation.document_id, citation.page_number);

  return (
    <div
      className="citation-card"
      onClick={() => onImageClick(citation.document_id, citation.page_number)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onImageClick(citation.document_id, citation.page_number);
        }
      }}
    >
      {/* Thumbnail */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="citation-thumbnail"
        src={thumbnailSrc}
        alt={`${citation.document_name} page ${citation.page_number}`}
        loading="lazy"
        onError={(e) => {
          // Replace broken image with a placeholder div containing a clean SVG
          const target = e.currentTarget;
          target.style.display = 'none';
          const placeholder = document.createElement('div');
          placeholder.className = 'citation-thumbnail';
          placeholder.style.display = 'flex';
          placeholder.style.alignItems = 'center';
          placeholder.style.justifyContent = 'center';
          placeholder.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-muted);">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          `;
          target.parentElement?.insertBefore(placeholder, target);
        }}
      />

      {/* Info */}
      <div className="citation-info">
        <div className="citation-doc-name" title={citation.document_name}>
          {citation.document_name}
        </div>
        <div className="citation-page-badge">Page {citation.page_number}</div>
        {citation.snippet && (
          <div className="citation-snippet">{citation.snippet}</div>
        )}
      </div>
    </div>
  );
}
