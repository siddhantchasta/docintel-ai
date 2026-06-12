"""
Embedding & vector-storage service.

Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings and
ChromaDB (persistent) for vector search.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000       # ~500 tokens
CHUNK_OVERLAP = 200
COLLECTION_NAME = "documents"


@dataclass
class Chunk:
    """A single text chunk with its metadata."""
    text: str
    doc_id: str
    doc_name: str
    page_number: int
    chunk_index: int


class EmbedderService:
    """
    Singleton service for embedding text and storing / searching in ChromaDB.
    Thread-safe via a lock around model loading.
    """

    _instance: Optional["EmbedderService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmbedderService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialised = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._model = None
        self._chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self._collection = self._chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._initialised = True
        logger.info(
            "EmbedderService ready — collection '%s' has %d items.",
            COLLECTION_NAME,
            self._collection.count(),
        )

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info("Loading embedding model '%s' lazily …", settings.EMBEDDING_MODEL)
                    self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
                    logger.info("Embedding model loaded successfully.")
        return self._model

    # ── Chunking ──────────────────────────────────────────────────────────

    @staticmethod
    def chunk_text(
        text: str,
        page_num: int,
        doc_id: str,
        doc_name: str,
    ) -> list[Chunk]:
        """Split *text* into overlapping chunks of ~CHUNK_SIZE characters."""
        if not text or not text.strip():
            return []

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            # Try to break at last sentence/newline boundary inside chunk
            if end < len(text):
                for sep in ("\n\n", "\n", ". ", " "):
                    last = chunk_text.rfind(sep)
                    if last > CHUNK_SIZE // 2:
                        chunk_text = chunk_text[: last + len(sep)]
                        break

            chunks.append(
                Chunk(
                    text=chunk_text.strip(),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    page_number=page_num,
                    chunk_index=idx,
                )
            )
            idx += 1
            start += len(chunk_text) - CHUNK_OVERLAP
            if start <= (end - CHUNK_SIZE):  # avoid infinite loop on tiny text
                break

        return chunks

    # ── Embed & store ─────────────────────────────────────────────────────

    def embed_and_store(self, chunks: list[Chunk]) -> int:
        """Encode *chunks*, store them in ChromaDB. Returns count stored."""
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
        import gc
        gc.collect()

        ids = [
            f"{c.doc_id}_p{c.page_number}_c{c.chunk_index}"
            for c in chunks
        ]
        metadatas = [
            {
                "doc_id": c.doc_id,
                "doc_name": c.doc_name,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        # Upsert in batches of 500
        batch = 500
        for i in range(0, len(ids), batch):
            self._collection.upsert(
                ids=ids[i : i + batch],
                embeddings=embeddings[i : i + batch],
                documents=texts[i : i + batch],
                metadatas=metadatas[i : i + batch],
            )

        logger.info("Stored %d chunks for doc %s.", len(chunks), chunks[0].doc_id)
        return len(chunks)

    # ── Search ────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Embed *query* and return top-k similar chunks from ChromaDB.

        Each result dict: {text, doc_id, doc_name, page_number, distance}.
        """
        if self._collection.count() == 0:
            return []

        query_embedding = self.model.encode([query], show_progress_bar=False).tolist()
        import gc
        gc.collect()

        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict[str, Any]] = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                hits.append(
                    {
                        "text": doc,
                        "doc_id": meta["doc_id"],
                        "doc_name": meta["doc_name"],
                        "page_number": meta["page_number"],
                        "distance": dist,
                    }
                )

        return hits

    # ── Utility ───────────────────────────────────────────────────────────

    def delete_document(self, doc_id: str) -> None:
        """Remove all chunks belonging to *doc_id*."""
        try:
            # ChromaDB where filter
            self._collection.delete(where={"doc_id": doc_id})
            logger.info("Deleted chunks for doc %s.", doc_id)
        except Exception as exc:
            logger.warning("Could not delete chunks for doc %s: %s", doc_id, exc)
