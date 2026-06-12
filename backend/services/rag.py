"""
RAG (Retrieval-Augmented Generation) query service.

Retrieves relevant chunks from ChromaDB, builds a grounded prompt,
calls Gemini 2.0 Flash, and parses citations from the response.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from google import genai

from config import settings
from models.schemas import ChatMessage, ChatResponse, Citation
from services.embedder import EmbedderService

logger = logging.getLogger(__name__)

# Cosine distance threshold — ChromaDB returns *distance* where lower = more similar.
# For cosine space, distance = 1 - similarity, so distance < 0.7 means similarity > 0.3.
_MAX_DISTANCE = 0.7

_RAG_PROMPT = """You are a document analysis assistant. Answer the user's question using ONLY the provided context chunks.

Rules:
1. Every claim must cite its source as [DocumentName, Page X].
2. If multiple chunks support an answer, cite all relevant sources.
3. If no relevant information exists in the context, respond: "I don't have enough information in the uploaded documents to answer this question."
4. Never make up information not present in the context.
5. Be concise and direct.

Context Chunks:
{chunks}

Conversation History:
{history}

User Question: {question}
"""


def _format_chunks(hits: list[dict[str, Any]]) -> str:
    """Format search hits into a numbered list for the prompt."""
    parts: list[str] = []
    for i, h in enumerate(hits, 1):
        parts.append(
            f"[Chunk {i}] Source: {h['doc_name']}, Page {h['page_number']}\n{h['text']}"
        )
    return "\n\n".join(parts)


def _format_history(history: list[ChatMessage]) -> str:
    """Format conversation history into readable text."""
    if not history:
        return "(none)"
    lines: list[str] = []
    for msg in history:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def _extract_citations(
    answer: str, hits: list[dict[str, Any]]
) -> list[Citation]:
    """
    Parse inline citations like [DocName, Page X] from the answer and
    build structured Citation objects using the search hits.
    """
    # Pattern: [SomeName, Page 3]
    pattern = re.compile(r"\[([^,\]]+),\s*Page\s*(\d+)\]", re.IGNORECASE)
    seen: set[tuple[str, int]] = set()
    citations: list[Citation] = []

    for match in pattern.finditer(answer):
        doc_name = match.group(1).strip()
        page_num = int(match.group(2))
        key = (doc_name.lower(), page_num)
        if key in seen:
            continue
        seen.add(key)

        # Find matching hit for snippet & doc_id
        best_hit: dict[str, Any] | None = None
        for h in hits:
            if (
                h["doc_name"].lower() == doc_name.lower()
                and h["page_number"] == page_num
            ):
                best_hit = h
                break

        # Fallback: match by doc_name only
        if best_hit is None:
            for h in hits:
                if h["doc_name"].lower() == doc_name.lower():
                    best_hit = h
                    break

        if best_hit:
            snippet = best_hit["text"][:300]
        else:
            snippet = ""

        citations.append(
            Citation(
                document_id=best_hit["doc_id"] if best_hit else "",
                document_name=doc_name,
                page_number=page_num,
                snippet=snippet,
            )
        )

    # If no inline citations were parsed but we have hits, create citations
    # from the top hits that were used to generate the answer.
    if not citations and hits:
        for h in hits[:3]:
            citations.append(
                Citation(
                    document_id=h["doc_id"],
                    document_name=h["doc_name"],
                    page_number=h["page_number"],
                    snippet=h["text"][:300],
                )
            )

    return citations


def rag_query(
    message: str,
    conversation_history: list[ChatMessage],
    embedder_service: EmbedderService,
) -> ChatResponse:
    """
    Full RAG pipeline:
      1. Search ChromaDB for relevant chunks.
      2. Check relevance threshold.
      3. Build grounded prompt.
      4. Call Gemini for answer.
      5. Extract citations.

    Returns ChatResponse(answer=..., citations=[...]).
    """
    # 1. Search
    hits = embedder_service.search(message, top_k=5)
    logger.info("RAG search returned %d hits for query: %s", len(hits), message[:80])

    # Log detailed information about retrieved chunks and similarity scores
    if hits:
        scores_log = ", ".join(
            f"'{h['doc_name']}' p{h['page_number']} (dist: {h['distance']:.4f}, similarity: {1 - h['distance']:.4f})"
            for h in hits
        )
        logger.info("Retrieved chunk similarity details: %s", scores_log)
    else:
        logger.info("No chunks retrieved from database.")

    # 2. Relevance check
    # We proceed if there is any retrieved context in the database.
    # If the database is completely empty (no documents indexed), we skip generation.
    if not hits:
        reason = "No context chunks retrieved from the database."
        logger.info("Gemini generation skipped. Reason: %s", reason)
        return ChatResponse(
            answer="I don't have enough information in the uploaded documents to answer this question.",
            citations=[],
        )

    # Filter to only relevant hits based on similarity threshold
    relevant_hits = [h for h in hits if h["distance"] <= _MAX_DISTANCE]
    if not relevant_hits:
        # If no hits meet the strict threshold, fall back to all retrieved hits
        # (crucial for generic summary/comparison queries that have higher distances)
        logger.info(
            "No chunks met similarity threshold (dist <= %f). Falling back to all %d retrieved hits to allow summary/comparison.",
            _MAX_DISTANCE,
            len(hits)
        )
        relevant_hits = hits
    else:
        logger.info(
            "%d out of %d chunks met similarity threshold (dist <= %f). Using them as context.",
            len(relevant_hits),
            len(hits),
            _MAX_DISTANCE
        )

    # 3. Build prompt
    chunks_text = _format_chunks(relevant_hits)
    history_text = _format_history(conversation_history)
    prompt = _RAG_PROMPT.format(
        chunks=chunks_text,
        history=history_text,
        question=message,
    )

    # 4. Call Gemini
    if not settings.GEMINI_API_KEY:
        reason = "GEMINI_API_KEY is not configured."
        logger.info("Gemini generation skipped. Reason: %s", reason)
        return ChatResponse(
            answer="LLM service unavailable (GEMINI_API_KEY not configured).",
            citations=[],
        )

    logger.info("Triggering Gemini generation with %d context chunks...", len(relevant_hits))
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
        )
        answer = response.text or "No response generated."
    except Exception as exc:
        logger.error("Gemini RAG call failed: %s", exc, exc_info=True)
        return ChatResponse(
            answer=f"An error occurred while generating the answer: {exc}",
            citations=[],
        )

    # 5. Extract citations
    citations = _extract_citations(answer, relevant_hits)

    return ChatResponse(answer=answer, citations=citations)
