"""
Upload API routes.

POST /api/upload         — Upload one or more files
GET  /api/upload/status/{document_id}  — Poll processing status
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.database import Document, Page, async_session_factory
from models.schemas import (
    DocumentStatus,
    UploadedDocumentInfo,
    UploadResponse,
)
from services.classifier import classify_document
from services.embedder import EmbedderService
from services.parser import parse_document
from services.security import (
    generate_storage_path,
    sanitize_filename,
    validate_file,
    verify_api_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


# ── Background processing pipeline ──────────────────────────────────────────

def _process_document(doc_id: str, file_path: str, original_filename: str) -> None:
    """
    Synchronous background task that runs the full processing pipeline:
    parse → classify → embed/index.

    Runs in a thread via FastAPI BackgroundTasks.
    """
    import asyncio

    async def _run() -> None:
        async with async_session_factory() as session:
            try:
                # ── 1. PARSING ────────────────────────────────────────
                await _update_status(session, doc_id, "parsing")

                storage_dir = generate_storage_path(doc_id)
                pages = parse_document(file_path, doc_id, storage_dir)

                # Save pages to DB
                for p in pages:
                    session.add(
                        Page(
                            document_id=doc_id,
                            page_number=p.page_number,
                            text_content=p.text_content,
                            has_tables=p.has_tables,
                            thumbnail_path=p.thumbnail_path,
                            full_image_path=p.full_image_path,
                        )
                    )

                # Update page count
                stmt = select(Document).where(Document.id == doc_id)
                result = await session.execute(stmt)
                doc = result.scalar_one()
                doc.page_count = len(pages)
                await session.commit()

                # ── 2. CLASSIFYING ────────────────────────────────────
                await _update_status(session, doc_id, "classifying")

                combined_text = "\n\n".join(p.text_content for p in pages if p.text_content)
                classification = classify_document(combined_text, original_filename)

                stmt = select(Document).where(Document.id == doc_id)
                result = await session.execute(stmt)
                doc = result.scalar_one()
                doc.classification = classification.model_dump()
                await session.commit()

                # ── 3. INDEXING ───────────────────────────────────────
                await _update_status(session, doc_id, "indexing")

                embedder = EmbedderService()
                all_chunks = []
                for p in pages:
                    if p.text_content:
                        chunks = EmbedderService.chunk_text(
                            p.text_content, p.page_number, doc_id, original_filename
                        )
                        all_chunks.extend(chunks)

                if all_chunks:
                    embedder.embed_and_store(all_chunks)

                # ── 4. DONE ──────────────────────────────────────────
                await _update_status(session, doc_id, "indexed")
                logger.info("Document %s processing complete.", doc_id)

            except Exception as exc:
                logger.error("Processing failed for %s: %s", doc_id, exc, exc_info=True)
                try:
                    await _update_status(session, doc_id, "error", str(exc))
                except Exception:
                    logger.error("Could not update error status for %s", doc_id)

    # Run the async pipeline in a new event loop (we're in a thread)
    asyncio.run(_run())


async def _update_status(
    session: AsyncSession, doc_id: str, new_status: str, error_msg: str | None = None
) -> None:
    stmt = select(Document).where(Document.id == doc_id)
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc:
        doc.status = new_status
        if error_msg is not None:
            doc.error_message = error_msg
        await session.commit()
    logger.info("Document %s → %s", doc_id, new_status)


# ── POST /api/upload ─────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    _api_key: str | None = Depends(verify_api_key),
) -> UploadResponse:
    """Upload one or more files and trigger background processing."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    uploaded: list[UploadedDocumentInfo] = []

    async with async_session_factory() as session:
        for file in files:
            # Validate
            content = await validate_file(file)

            doc_id = str(uuid.uuid4())
            safe_name = sanitize_filename(file.filename or "unknown")
            storage_dir = generate_storage_path(doc_id)

            # Save raw file to disk
            saved_path = storage_dir / safe_name
            saved_path.write_bytes(content)

            # Create DB record
            doc = Document(
                id=doc_id,
                filename=safe_name,
                original_filename=file.filename or safe_name,
                status="uploading",
                file_size=len(content),
            )
            session.add(doc)
            await session.commit()

            # Queue background processing
            background_tasks.add_task(
                _process_document, doc_id, str(saved_path), file.filename or safe_name
            )

            uploaded.append(
                UploadedDocumentInfo(id=doc_id, filename=file.filename or safe_name, status="uploading")
            )

    return UploadResponse(documents=uploaded)


# ── GET /api/upload/status/{document_id} ─────────────────────────────────────

@router.get("/upload/status/{document_id}", response_model=DocumentStatus)
async def get_upload_status(
    document_id: str,
    _api_key: str | None = Depends(verify_api_key),
) -> DocumentStatus:
    """Return the current processing status of a document."""
    async with async_session_factory() as session:
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return DocumentStatus(
        id=doc.id,
        filename=doc.original_filename,
        status=doc.status,
        classification=doc.classification,
        page_count=doc.page_count,
        error=doc.error_message,
    )
