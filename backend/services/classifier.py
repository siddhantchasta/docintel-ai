"""
Document classification service using Google Gemini 2.0 Flash.

Takes extracted text content and filename, returns a structured
ClassificationResult via LLM JSON output.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from google import genai

from config import settings
from models.schemas import ClassificationResult

logger = logging.getLogger(__name__)

# Maximum characters of document text to send for classification
_MAX_CHARS = 3000

_CLASSIFICATION_PROMPT = """You are a document classification engine. Analyse the following document content and filename, then return a JSON object with exactly these fields:

{{
  "document_type": "invoice|contract|report|letter|form|research_paper|manual|other",
  "topic": "finance|legal|medical|technical|education|government|general|other",
  "content_characteristics": ["has_tables", "has_images", "handwritten", "scanned", "multi_page"],
  "sensitivity_level": "public|internal|confidential|highly_confidential",
  "language": "<ISO 639-1 code>",
  "summary": "Brief 1-2 sentence summary of the document",
  "key_entities": ["entity1", "entity2"]
}}

Rules:
- content_characteristics should only include applicable items from the list above.
- key_entities should list the top 3-5 important named entities (people, organisations, dates, monetary amounts).
- Return ONLY the JSON object, no extra text.

Filename: {filename}

Document Content (first {max_chars} chars):
\"\"\"
{content}
\"\"\"
"""


def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from raw LLM output."""
    # Try direct parse first
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try to find JSON block in markdown fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: find first { … } pair
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract JSON from LLM response")


def classify_document(text_content: str, filename: str) -> ClassificationResult:
    """
    Classify a document using Gemini 2.0 Flash.

    Args:
        text_content: concatenated text from all pages.
        filename: original filename for hints.

    Returns:
        ClassificationResult with structured metadata.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — returning default classification.")
        return ClassificationResult(summary="Classification skipped (no API key).")

    truncated = text_content[:_MAX_CHARS]
    prompt = _CLASSIFICATION_PROMPT.format(
        filename=filename,
        max_chars=_MAX_CHARS,
        content=truncated,
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
        )

        raw_text = response.text or ""
        logger.debug("Gemini classification raw response: %s", raw_text[:500])

        data = _extract_json(raw_text)
        return ClassificationResult(**data)

    except Exception as exc:
        logger.error("Classification failed: %s", exc, exc_info=True)
        return ClassificationResult(
            summary=f"Classification failed: {exc}",
        )
