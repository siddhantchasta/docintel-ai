import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="landing">
      {/* Hero */}
      <div className="landing-hero animate-fade-in-up">
        <div className="landing-icon">
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ color: 'var(--text-secondary)' }}
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <line x1="10" y1="9" x2="8" y2="9" />
          </svg>
        </div>
        <h1>Document intelligence workspace</h1>
        <p>
          Upload and index documents to extract structured insights and run cited chat queries against your files.
        </p>
      </div>

      {/* CTA Cards */}
      <div className="landing-cards">
        <Link href="/chat" className="landing-card">
          <div className="landing-card-icon">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ color: 'var(--text-secondary)' }}
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h2>Interactive query console</h2>
          <p>
            Query index records and chat with documents with detailed inline page citations.
          </p>
          <span className="landing-card-arrow">Open workspace →</span>
        </Link>

        <Link href="/upload" className="landing-card">
          <div className="landing-card-icon">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ color: 'var(--text-secondary)' }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h2>Document intake & processing</h2>
          <p>
            Upload source PDFs and images to parse metadata, classify content, and build indexes.
          </p>
          <span className="landing-card-arrow">Upload documents →</span>
        </Link>
      </div>
    </div>
  );
}
