"""
Pydantic request / response schemas for every API endpoint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Classification ────────────────────────────────────────────────────────────

class ClassificationResult(BaseModel):
    document_type: str = "other"
    topic: str = "general"
    content_characteristics: list[str] = Field(default_factory=list)
    sensitivity_level: str = "public"
    language: str = "en"
    summary: str = ""
    key_entities: list[str] = Field(default_factory=list)


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadedDocumentInfo(BaseModel):
    id: str
    filename: str
    status: str


class UploadResponse(BaseModel):
    documents: list[UploadedDocumentInfo]


# ── Document status / listing ────────────────────────────────────────────────

class DocumentStatus(BaseModel):
    id: str
    filename: str
    status: str
    classification: Optional[dict[str, Any]] = None
    page_count: Optional[int] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    id: str
    filename: str
    status: str
    classification: Optional[dict[str, Any]] = None
    page_count: Optional[int] = None
    uploaded_at: Optional[str] = None
    file_size: Optional[int] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


# ── Chat / RAG ────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
