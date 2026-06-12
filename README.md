# 🧠 DocIntel AI

> **Document Intelligence + Agentic RAG** — Upload messy, real-world documents, extract their content with OCR, classify them with AI, and chat with a citation-grounded assistant.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-LLM-purple)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              Next.js 16 Frontend (TypeScript)        │
│   ┌──────────────┐      ┌──────────────────────────┐ │
│   │  /upload      │      │  /chat                   │ │
│   │  Bulk Upload  │      │  Chatbot + Citations     │ │
│   │  Status Track │      │  Thumbnails + Full Page  │ │
│   │  Drag & Drop  │      │  Voice Input (Bonus)     │ │
│   └──────────────┘      └──────────────────────────┘ │
└─────────────────────┬────────────────────────────────┘
                      │ REST API (JSON + multipart)
                      ▼
┌──────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11)            │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐ │
│  │ Upload   │ │  Parser  │ │Classify│ │ RAG Agent │ │
│  │  API     │ │ Service  │ │  Svc   │ │  + Chat   │ │
│  └──────────┘ └──────────┘ └────────┘ └───────────┘ │
│         │          │            │           │        │
│         ▼          ▼            ▼           ▼        │
│  ┌──────────────────────────────────────────────┐    │
│  │              Data Layer                       │   │
│  │  ChromaDB (vectors) │ SQLite (metadata)       │   │
│  │  /storage (files)   │ /thumbnails (images)    │   │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Pipeline Flow

1. **Upload** → Files validated (MIME type, extension, size) → saved with UUID paths
2. **Parse** → `pdfplumber` extracts text + tables as markdown → `pytesseract` OCR fallback for scans → `pdf2image` renders page thumbnails
3. **Classify** → Gemini 2.5 Flash classifies across 7 dimensions → structured JSON
4. **Index** → `sentence-transformers` embeds text chunks → stored in ChromaDB
5. **Chat** → Query embedded → top-K retrieval → Gemini generates cited answer → citations extracted

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Tesseract OCR (`brew install tesseract` on macOS)
- Poppler (`brew install poppler` on macOS)
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier)

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/docintel-ai.git
cd docintel-ai
cp .env.example .env
```

Edit `.env` and add your API keys:
```
GEMINI_API_KEY=your-gemini-api-key
API_KEY=your-chosen-secret-key
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Seed Sample Documents

```bash
python seed.py
```

This processes the 6 included sample documents (invoice, contract, research paper, financial report, government policy, medical lab report) so the chatbot works on first run.

### 4. Start Backend

```bash
python main.py
# → Backend running at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### 5. Frontend Setup

```bash
cd ../frontend
npm install
```

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-chosen-secret-key
```

### 6. Start Frontend

```bash
npm run dev
# → Frontend running at http://localhost:3000
```

---

## 📄 Sample Documents

6 diverse documents are included in `backend/sample_docs/`:

| Document | Type | Content | Purpose |
|----------|------|---------|---------|
| `sample_invoice.pdf` | Invoice | Line items, totals, payment info | Tests table extraction |
| `employment_contract.pdf` | Legal Contract | 8 sections, signatures | Tests multi-page text |
| `research_paper_transformers.pdf` | Research Paper | Abstract, results tables, references | Tests academic content + tables |
| `quarterly_financial_report.pdf` | Financial Report | Income statement, balance sheet | Tests complex table structures |
| `government_ai_policy.pdf` | Policy Document | Risk framework, compliance timeline | Tests government/regulatory content |
| `medical_lab_report.pdf` | Medical Report | CBC, CMP, lipid panel tables | Tests medical data + sensitivity |

---

## 🔒 Security Decisions

### ✅ Implemented

| Layer | Measure | Implementation |
|-------|---------|----------------|
| **Upload** | File type validation | MIME type detection via `python-magic` (magic bytes) + extension whitelist (pdf, png, jpg, tiff, bmp, webp) |
| **Upload** | File size limit | 20MB max per file, checked before saving |
| **Upload** | Filename sanitization | Path components stripped, special chars replaced, UUID-based storage paths prevent traversal |
| **Storage** | UUID-based isolation | Files stored at `storage/{uuid}/`, never using user-supplied filenames on disk |
| **Storage** | No direct file serving | Thumbnails and page images served through validated API endpoints, not static files |
| **Processing** | Page count limits | Max 50 pages per document to prevent resource exhaustion |
| **Processing** | Error isolation | Each document processed in try/except — failures don't crash other uploads |
| **Processing** | Prompt injection mitigation | System prompt and user content strictly separated in LLM calls. Document text placed in data section, not instructions. |
| **API** | API key authentication | All endpoints (except health) require `X-API-Key` header or `?api_key=` query parameter |
| **API** | Rate limiting | `slowapi` rate limiter — 60 requests/minute per IP (configurable) |
| **API** | CORS restriction | Only whitelisted frontend origins allowed |
| **API** | Input validation | Pydantic schemas enforce types, lengths, and required fields on all inputs |
| **Code** | No secrets in code | All secrets loaded from environment variables. `.env.example` provided without values. |
| **Code** | Global error handler | Unhandled exceptions return generic 500 — no stack traces or internal details leaked |

### 🤔 Considered but Skipped (Time Constraints)

| Measure | Reason Skipped |
|---------|----------------|
| **Encryption at rest** | Would require encrypted volumes or field-level encryption; excessive for demo |
| **Virus/malware scanning** | Would integrate ClamAV but requires system-level binary installation |
| **JWT-based user authentication** | Assessment doesn't require multi-user support; API key is sufficient |
| **Document-level access control** | Single-user demo; all documents belong to the same knowledge base |
| **Audit logging** | Logging exists but no formal audit trail with timestamps/user IDs |

### 🚀 Would Add Given More Time

- **ClamAV integration** for malware scanning on upload
- **JWT/OAuth authentication** for multi-user support
- **Document-level ACLs** — associate documents with users/roles
- **Encrypted storage** using AES-256 for documents at rest
- **Content redaction** — ability to redact sensitive entities before embedding
- **HTTPS enforcement** at the application level (currently handled by deployment platform)
- **WAF/request filtering** for production deployment

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload files (multipart) |
| `GET` | `/api/upload/status/{id}` | Check processing status |
| `POST` | `/api/chat` | Send chat message with RAG |
| `GET` | `/api/documents` | List all documents |
| `GET` | `/api/documents/{id}` | Get document details |
| `GET` | `/api/pages/{id}/{page}/thumbnail` | Page thumbnail (200px PNG) |
| `GET` | `/api/pages/{id}/{page}/full` | Full page image (PNG) |

Interactive API docs available at `/docs` when running the backend.

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Backend Framework | FastAPI 0.115 | Async, auto-docs, Pydantic validation |
| PDF Text + Tables | pdfplumber | Best table extraction, free |
| PDF → Images | pdf2image | Reliable poppler wrapper |
| OCR | pytesseract | Free Tesseract wrapper |
| Vector Database | ChromaDB | Embedded, zero-config, persistent |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Free, local, fast, 80MB |
| LLM | Google Gemini 2.5 Flash | Free tier, high quality |
| Metadata DB | SQLite (async) | Zero-config, file-based |
| Rate Limiting | slowapi | Simple FastAPI middleware |
| File Validation | python-magic | MIME detection via libmagic |
| Frontend | Next.js 16 + TypeScript | Required by assessment |
| Styling | Vanilla CSS | Premium dark theme, glassmorphism |
| Voice Input | Web Speech API | Browser-native, free (bonus) |

---

## 📁 Project Structure

```
docintel-ai/
├── .env.example                  # Environment variables template
├── .gitignore
├── render.yaml                   # Render deployment config
├── README.md
│
├── backend/
│   ├── Dockerfile                # Docker build for deployment
│   ├── requirements.txt          # Python dependencies
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Settings from env vars
│   ├── seed.py                   # Seed script for sample docs
│   │
│   ├── api/                      # API route handlers
│   │   ├── upload.py             # Upload + background processing
│   │   ├── chat.py               # RAG chat endpoint
│   │   ├── documents.py          # Document listing
│   │   └── pages.py              # Page image serving
│   │
│   ├── services/                 # Business logic
│   │   ├── parser.py             # PDF parsing + OCR + tables
│   │   ├── classifier.py         # LLM document classification
│   │   ├── embedder.py           # Chunking + embedding + ChromaDB
│   │   ├── rag.py                # RAG pipeline + citation extraction
│   │   └── security.py           # File validation + auth
│   │
│   ├── models/                   # Data models
│   │   ├── database.py           # SQLAlchemy async models
│   │   └── schemas.py            # Pydantic request/response schemas
│   │
│   └── sample_docs/              # 6 diverse sample PDFs
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx        # Root layout with nav
    │   │   ├── page.tsx          # Landing page
    │   │   ├── globals.css       # Premium dark theme CSS
    │   │   ├── chat/page.tsx     # Chat interface
    │   │   └── upload/page.tsx   # Bulk upload page
    │   │
    │   ├── components/
    │   │   ├── Navbar.tsx        # Navigation bar
    │   │   ├── ChatMessage.tsx   # Chat bubble with citations
    │   │   ├── CitationCard.tsx  # Clickable citation thumbnail
    │   │   ├── ImageModal.tsx    # Full-page image viewer
    │   │   ├── FileUploader.tsx  # Drag-and-drop uploader
    │   │   ├── UploadStatus.tsx  # Per-file status tracker
    │   │   └── VoiceInput.tsx    # Voice input (bonus)
    │   │
    │   ├── lib/api.ts            # API client
    │   └── types/index.ts        # TypeScript interfaces
    │
    └── .env.local.example        # Frontend env template
```

---

## 🎯 Classification Schema

Each document is classified into a structured JSON with 7 dimensions:

```json
{
  "document_type": "invoice | contract | report | research_paper | ...",
  "topic": "finance | legal | medical | technical | ...",
  "content_characteristics": ["has_tables", "scanned", "multi_page", ...],
  "sensitivity_level": "public | internal | confidential | highly_confidential",
  "language": "en",
  "summary": "Brief 1-2 sentence summary",
  "key_entities": ["TechVision Solutions", "$44,051.00", ...]
}
```

---

## 🚀 Deployment

### Backend (Render)
- Docker-based deployment with system dependencies (Tesseract, Poppler)
- Persistent disk for ChromaDB and document storage
- `render.yaml` included for one-click deploy

### Frontend (Vercel)
- Standard Next.js deployment
- Set `NEXT_PUBLIC_API_URL` to your Render backend URL
- Set `NEXT_PUBLIC_API_KEY` to match your backend API key

---

## 📜 License

MIT
