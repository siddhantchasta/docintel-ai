'use client';

import type { Message } from '@/types';
import CitationCard from '@/components/CitationCard';
import { type ReactNode } from 'react';

interface ChatMessageProps {
  message: Message;
  onImageClick: (docId: string, pageNum: number, docName: string) => void;
}

/**
 * Formats the message text:
 * - Splits into paragraphs on double newlines
 * - Highlights inline citations like [DocName, Page 3]
 */
function formatContent(text: string): ReactNode[] {
  const paragraphs = text.split(/\n{2,}/);

  return paragraphs.map((para, pIdx) => {
    // Match patterns like [DocName, Page X] or [Doc Name, Page 12]
    const parts: ReactNode[] = [];
    const regex = /\[([^\]]+?,\s*Page\s*\d+)\]/gi;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(para)) !== null) {
      // Text before match
      if (match.index > lastIndex) {
        parts.push(para.slice(lastIndex, match.index));
      }
      // Highlighted citation
      parts.push(
        <span key={`${pIdx}-${match.index}`} className="inline-citation">
          {match[1]}
        </span>,
      );
      lastIndex = match.index + match[0].length;
    }

    // Remaining text
    if (lastIndex < para.length) {
      parts.push(para.slice(lastIndex));
    }

    return (
      <p key={pIdx}>
        {parts.length > 0 ? parts : para}
      </p>
    );
  });
}

export default function ChatMessage({ message, onImageClick }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-avatar">
        {isUser ? 'U' : 'AI'}
      </div>
      <div className="message-body">
        <div className="message-bubble">
          {formatContent(message.content)}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div>
            <div className="citations-label">
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ display: 'inline-block', verticalAlign: 'middle' }}
              >
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span>Sources</span>
            </div>
            <div className="citations-container">
              {message.citations.map((citation, idx) => (
                <CitationCard
                  key={`${citation.document_id}-${citation.page_number}-${idx}`}
                  citation={citation}
                  onImageClick={(docId, pageNum) =>
                    onImageClick(docId, pageNum, citation.document_name)
                  }
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
