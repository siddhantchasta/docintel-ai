'use client';

import { useState, useRef, useEffect, useCallback, type FormEvent } from 'react';
import type { Message } from '@/types';
import { sendMessage as sendChatMessage } from '@/lib/api';
import ChatMessage from '@/components/ChatMessage';
import ImageModal from '@/components/ImageModal';
import VoiceInput from '@/components/VoiceInput';
import { getFullImageUrl } from '@/lib/api';

const SUGGESTIONS = [
  'Summarize the key findings in my documents',
  'What are the main topics covered?',
  'Compare the documents I uploaded',
  'Extract all dates and deadlines mentioned',
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Image modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalImage, setModalImage] = useState('');
  const [modalDocName, setModalDocName] = useState('');
  const [modalPage, setModalPage] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
    }
  }, [input]);

  async function handleSend(e?: FormEvent) {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage: Message = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const history = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChatMessage(trimmed, history);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error processing your request. ${err instanceof Error ? err.message : 'Please try again.'}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSuggestionClick(suggestion: string) {
    setInput(suggestion);
    // Send immediately
    const userMessage: Message = { role: 'user', content: suggestion };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    sendChatMessage(suggestion, [{ role: 'user', content: suggestion }])
      .then((response) => {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.answer,
          citations: response.citations,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      })
      .catch((err) => {
        const errorMsg: Message = {
          role: 'assistant',
          content: `Sorry, I encountered an error. ${err instanceof Error ? err.message : 'Please try again.'}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      })
      .finally(() => {
        setLoading(false);
        setInput('');
      });
  }

  function handleImageClick(docId: string, pageNum: number, docName: string) {
    setModalImage(getFullImageUrl(docId, pageNum));
    setModalDocName(docName);
    setModalPage(pageNum);
    setModalOpen(true);
  }

  function handleVoiceTranscript(text: string) {
    setInput(text);
    textareaRef.current?.focus();
  }

  const isEmpty = messages.length === 0;

  return (
    <>
      <div className="chat-container">
        {/* Messages area */}
        {isEmpty && !loading ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">🧠</div>
            <h2>What can I help you discover?</h2>
            <p>
              Ask me anything about your uploaded documents. I&apos;ll search
              through them and provide precise, cited answers.
            </p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="chat-suggestion-btn"
                  onClick={() => handleSuggestionClick(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                message={msg}
                onImageClick={handleImageClick}
              />
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="message message-assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-body">
                  <div className="message-bubble">
                    <div className="typing-indicator">
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input bar */}
        <form className="chat-input-bar" onSubmit={handleSend}>
          <div className="chat-input-wrapper">
            <VoiceInput onTranscript={handleVoiceTranscript} />
            <textarea
              ref={textareaRef}
              className="chat-input"
              placeholder="Ask a question about your documents…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
              aria-label="Send message"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </form>
      </div>

      {/* Image Modal */}
      <ImageModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        imageUrl={modalImage}
        documentName={modalDocName}
        pageNumber={modalPage}
      />
    </>
  );
}
