import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="landing">
      {/* Hero */}
      <div className="landing-hero animate-fade-in-up">
        <div className="landing-icon">🧠</div>
        <h1>Document Intelligence, Reimagined</h1>
        <p>
          Upload any document, let AI classify &amp; index it, then ask
          questions with fully-cited, context-aware answers — powered by
          agentic RAG.
        </p>
      </div>

      {/* CTA Cards */}
      <div className="landing-cards">
        <Link href="/chat" className="landing-card card-interactive">
          <div className="landing-card-icon">💬</div>
          <h2>Chat with Documents</h2>
          <p>
            Ask questions about your uploaded documents and get precise,
            cited answers in seconds.
          </p>
          <span className="landing-card-arrow">→</span>
        </Link>

        <Link href="/upload" className="landing-card card-interactive">
          <div className="landing-card-icon">📄</div>
          <h2>Upload Documents</h2>
          <p>
            Drag &amp; drop PDFs and images — AI will parse, classify, and
            index them automatically.
          </p>
          <span className="landing-card-arrow">→</span>
        </Link>
      </div>
    </div>
  );
}
