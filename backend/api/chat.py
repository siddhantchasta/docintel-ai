"""
Chat API route.

POST /api/chat — Send a message through the RAG pipeline.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import ChatRequest, ChatResponse
from services.embedder import EmbedderService
from services.rag import rag_query
from services.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _api_key: str | None = Depends(verify_api_key),
) -> ChatResponse:
    """
    Accept a user message (with optional conversation history),
    run the RAG pipeline, and return the answer with citations.
    """
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    embedder = EmbedderService()

    try:
        response = rag_query(
            message=body.message,
            conversation_history=body.conversation_history,
            embedder_service=embedder,
        )
    except Exception as exc:
        logger.error("Chat RAG query failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your question. Please try again.",
        )

    return response
