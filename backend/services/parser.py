"""
Document parsing service.

Extracts text, tables, and page images from PDFs and image files.
Uses pdfplumber for native text, pytesseract as OCR fallback,
and pdf2image for page rendering.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

from config import settings

logger = logging.getLogger(__name__)

THUMBNAIL_WIDTH = 200
MIN_NATIVE_TEXT_LENGTH = 50


@dataclass
class PageResult:
    """Extracted content for a single page."""
    page_number: int
    text_content: str = ""
    has_tables: bool = False
    table_text: str = ""
    thumbnail_path: Optional[str] = None
    full_image_path: Optional[str] = None


def _table_to_markdown(table: list[list[str | None]]) -> str:
    """Convert a pdfplumber table (list of rows) to markdown."""
    if not table:
        return ""
    rows: list[str] = []
    for i, row in enumerate(table):
        cells = [str(c) if c is not None else "" for c in row]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0:
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(rows)


def _save_images(
    pil_image: Image.Image, storage_dir: Path, page_num: int
) -> tuple[str, str]:
    """Save full-resolution and thumbnail images; return their paths."""
    full_path = storage_dir / f"page_{page_num}_full.png"
    thumb_path = storage_dir / f"page_{page_num}_thumb.png"

    # Full resolution
    pil_image.save(str(full_path), format="PNG")

    # Thumbnail (maintain aspect ratio)
    w, h = pil_image.size
    ratio = THUMBNAIL_WIDTH / w
    thumb_size = (THUMBNAIL_WIDTH, max(1, int(h * ratio)))
    thumb = pil_image.resize(thumb_size, Image.LANCZOS)
    thumb.save(str(thumb_path), format="PNG")

    return str(full_path), str(thumb_path)


def _parse_pdf(file_path: Path, doc_id: str, storage_dir: Path) -> list[PageResult]:
    """Parse a PDF file, returning a PageResult per page (up to MAX_PAGES)."""
    results: list[PageResult] = []

    # Render all pages as images first (for thumbnails / OCR fallback)
    try:
        images = convert_from_path(
            str(file_path),
            dpi=200,
            last_page=settings.MAX_PAGES,
        )
    except Exception as exc:
        logger.error("pdf2image conversion failed for %s: %s", doc_id, exc)
        images = []

    with pdfplumber.open(str(file_path)) as pdf:
        page_count = min(len(pdf.pages), settings.MAX_PAGES)

        for idx in range(page_count):
            page = pdf.pages[idx]
            page_num = idx + 1
            result = PageResult(page_number=page_num)

            # ── 1. Native text extraction ─────────────────────────────
            try:
                native_text = page.extract_text() or ""
            except Exception:
                native_text = ""

            # ── 2. OCR fallback ───────────────────────────────────────
            text = native_text
            if len(native_text.strip()) < MIN_NATIVE_TEXT_LENGTH and idx < len(images):
                try:
                    ocr_text = pytesseract.image_to_string(images[idx])
                    if len(ocr_text.strip()) > len(native_text.strip()):
                        text = ocr_text
                except Exception as exc:
                    logger.warning("OCR failed on page %d of %s: %s", page_num, doc_id, exc)

            # ── 3. Table extraction ───────────────────────────────────
            table_md = ""
            try:
                tables = page.extract_tables()
                if tables:
                    result.has_tables = True
                    table_md_parts = [_table_to_markdown(t) for t in tables]
                    table_md = "\n\n".join(table_md_parts)
            except Exception as exc:
                logger.warning("Table extraction failed on page %d of %s: %s", page_num, doc_id, exc)

            # Combine text + table markdown
            combined = text.strip()
            if table_md:
                combined += "\n\n[Tables]\n" + table_md
            result.text_content = combined

            # ── 4. Save page images ───────────────────────────────────
            if idx < len(images):
                try:
                    full_p, thumb_p = _save_images(images[idx], storage_dir, page_num)
                    result.full_image_path = full_p
                    result.thumbnail_path = thumb_p
                except Exception as exc:
                    logger.warning("Image save failed page %d of %s: %s", page_num, doc_id, exc)

            results.append(result)

    return results


def _parse_image(file_path: Path, doc_id: str, storage_dir: Path) -> list[PageResult]:
    """Parse a single image file using OCR."""
    result = PageResult(page_number=1)

    try:
        img = Image.open(str(file_path))
        # Ensure RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # OCR
        try:
            text = pytesseract.image_to_string(img)
            result.text_content = text.strip()
        except Exception as exc:
            logger.warning("OCR failed for image %s: %s", doc_id, exc)
            result.text_content = ""

        # Save images
        full_p, thumb_p = _save_images(img, storage_dir, 1)
        result.full_image_path = full_p
        result.thumbnail_path = thumb_p

    except Exception as exc:
        logger.error("Failed to open image %s: %s", doc_id, exc)
        raise

    return [result]


def parse_document(
    file_path: str | Path, doc_id: str, storage_dir: str | Path
) -> list[PageResult]:
    """
    Main entry point: parse a document (PDF or image) and return page results.

    Args:
        file_path: path to the uploaded file on disk.
        doc_id: the UUID for this document.
        storage_dir: directory to write page images into.

    Returns:
        List of PageResult, one per page.
    """
    file_path = Path(file_path)
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    ext = file_path.suffix.lower().lstrip(".")

    if ext == "pdf":
        return _parse_pdf(file_path, doc_id, storage_dir)
    elif ext in {"png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"}:
        return _parse_image(file_path, doc_id, storage_dir)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")
