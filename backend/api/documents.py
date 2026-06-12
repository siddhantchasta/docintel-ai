"""
Documents API routes.

GET /api/documents              — List all indexed documents
GET /api/documents/{document_id} — Get single document details
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Document, async_session_factory
from models.schemas import DocumentInfo, DocumentListResponse
from services.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    _api_key: str | None = Depends(verify_api_key),
) -> DocumentListResponse:
    """Return all documents ordered by upload time (newest first)."""
    async with async_session_factory() as session:
        stmt = select(Document).order_by(Document.uploaded_at.desc())
        result = await session.execute(stmt)
        docs = result.scalars().all()

    return DocumentListResponse(
        documents=[
            DocumentInfo(
                id=d.id,
                filename=d.original_filename,
                status=d.status,
                classification=d.classification,
                page_count=d.page_count,
                uploaded_at=d.uploaded_at.isoformat() if d.uploaded_at else None,
                file_size=d.file_size,
            )
            for d in docs
        ]
    )


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    _api_key: str | None = Depends(verify_api_key),
) -> DocumentInfo:
    """Return details for a single document."""
    async with async_session_factory() as session:
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return DocumentInfo(
        id=doc.id,
        filename=doc.original_filename,
        status=doc.status,
        classification=doc.classification,
        page_count=doc.page_count,
        uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        file_size=doc.file_size,
    )
