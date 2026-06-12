"""
Security utilities: file validation, filename sanitisation, API-key auth.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import magic
from fastapi import HTTPException, Request, UploadFile, status

from config import settings

logger = logging.getLogger(__name__)

# Map of allowed MIME types → canonical extensions
_ALLOWED_MIMES: dict[str, str] = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/tiff": "tiff",
    "image/bmp": "bmp",
    "image/webp": "webp",
}


# ── File validation ──────────────────────────────────────────────────────────

async def validate_file(file: UploadFile) -> bytes:
    """
    Read the uploaded file and validate:
      1. File is not empty.
      2. Extension is in the allow-list.
      3. MIME type (detected via libmagic) matches.
      4. Size does not exceed MAX_FILE_SIZE_MB.

    Returns the raw file bytes on success.
    Raises HTTPException(422) on any validation failure.
    """
    # Read content
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File '{file.filename}' is empty.",
        )

    # Extension check
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extension '.{ext}' is not allowed. Accepted: {settings.ALLOWED_EXTENSIONS}",
        )

    # MIME check via python-magic
    detected_mime = magic.from_buffer(content[:2048], mime=True)
    if detected_mime not in _ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Detected MIME type '{detected_mime}' is not allowed.",
        )

    # Size check
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB.",
        )

    return content


# ── Filename sanitisation ────────────────────────────────────────────────────

def sanitize_filename(filename: str) -> str:
    """Strip directory components and replace non-alphanumeric chars (except .-_)."""
    # Take only the basename
    name = os.path.basename(filename)
    # Replace anything that isn't alphanumeric, dot, hyphen, or underscore
    name = re.sub(r"[^\w.\-]", "_", name)
    # Collapse repeated underscores
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "unnamed_file"


# ── Storage path generation ──────────────────────────────────────────────────

def generate_storage_path(doc_id: str) -> Path:
    """
    Return a UUID-based directory under STORAGE_DIR and create it.
    e.g.  storage/<doc_id>/
    """
    path = settings.STORAGE_DIR / doc_id
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── API key auth dependency ──────────────────────────────────────────────────

async def verify_api_key(request: Request) -> Optional[str]:
    """
    FastAPI dependency.
    If settings.API_KEY is set, require either:
      • Header  `X-API-Key: <key>`
      • Query   `?api_key=<key>`
    If settings.API_KEY is empty, auth is disabled (returns None).
    """
    expected = settings.API_KEY
    if not expected:
        return None  # Auth disabled

    provided = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return provided
