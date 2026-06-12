"""
Pages API routes — serve page thumbnails and full-resolution images.

GET /api/pages/{document_id}/{page_num}/thumbnail — 200px-wide PNG
GET /api/pages/{document_id}/{page_num}/full      — Full resolution PNG
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Document, Page, async_session_factory
from services.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pages"])


async def _get_page(document_id: str, page_num: int) -> Page:
    """Fetch a Page record or raise 404."""
    async with async_session_factory() as session:
        # Verify document exists
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )

        # Fetch the page
        stmt = select(Page).where(
            Page.document_id == document_id, Page.page_number == page_num
        )
        result = await session.execute(stmt)
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_num} not found for document {document_id}.",
            )

        return page


@router.get("/pages/{document_id}/{page_num}/thumbnail")
async def get_thumbnail(
    document_id: str,
    page_num: int,
    _api_key: str | None = Depends(verify_api_key),
) -> FileResponse:
    """Serve a 200px-wide thumbnail PNG for the requested page."""
    page = await _get_page(document_id, page_num)

    if not page.thumbnail_path or not Path(page.thumbnail_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not available."
        )

    return FileResponse(
        page.thumbnail_path,
        media_type="image/png",
        filename=f"{document_id}_p{page_num}_thumb.png",
    )


@router.get("/pages/{document_id}/{page_num}/full")
async def get_full_image(
    document_id: str,
    page_num: int,
    _api_key: str | None = Depends(verify_api_key),
) -> FileResponse:
    """Serve the full-resolution PNG for the requested page."""
    page = await _get_page(document_id, page_num)

    if not page.full_image_path or not Path(page.full_image_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Full image not available."
        )

    return FileResponse(
        page.full_image_path,
        media_type="image/png",
        filename=f"{document_id}_p{page_num}_full.png",
    )
