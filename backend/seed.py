#!/usr/bin/env python3
"""
Seed script — processes all files found in a local ``sample_docs/`` directory.

Usage:
    cd backend/
    python seed.py                       # process ./sample_docs/*
    python seed.py /path/to/docs_dir     # process custom directory

For each supported file the script:
  1. Saves a copy under storage/<doc_id>/
  2. Creates a Document row (SQLite)
  3. Parses pages (text + images)
  4. Classifies the document via Gemini
  5. Embeds & indexes all chunks in ChromaDB
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from pathlib import Path

# ── Bootstrap ────────────────────────────────────────────────────────────────
# Ensure the backend package is importable when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings  # noqa: E402
from models.database import Document, Page, async_session_factory, init_db  # noqa: E402
from services.classifier import classify_document  # noqa: E402
from services.embedder import EmbedderService  # noqa: E402
from services.parser import parse_document  # noqa: E402
from services.security import generate_storage_path, sanitize_filename  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("seed")


async def seed_file(file_path: Path, embedder: EmbedderService) -> bool:
    """Process a single file end-to-end. Returns True on success."""
    doc_id = str(uuid.uuid4())
    safe_name = sanitize_filename(file_path.name)
    original_name = file_path.name

    logger.info("── Processing: %s  (id=%s)", original_name, doc_id)

    # 1. Copy file into storage
    storage_dir = generate_storage_path(doc_id)
    dest = storage_dir / safe_name
    dest.write_bytes(file_path.read_bytes())
    file_size = file_path.stat().st_size

    async with async_session_factory() as session:
        # Create DB record
        doc = Document(
            id=doc_id,
            filename=safe_name,
            original_filename=original_name,
            status="parsing",
            file_size=file_size,
        )
        session.add(doc)
        await session.commit()

        try:
            # 2. Parse
            logger.info("   Parsing …")
            pages = parse_document(str(dest), doc_id, storage_dir)
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
            doc.page_count = len(pages)
            doc.status = "classifying"
            await session.commit()
            logger.info("   Parsed %d page(s).", len(pages))

            # 3. Classify
            logger.info("   Classifying …")
            combined = "\n\n".join(p.text_content for p in pages if p.text_content)
            classification = classify_document(combined, original_name)
            doc.classification = classification.model_dump()
            doc.status = "indexing"
            await session.commit()
            logger.info("   Classified as: %s / %s", classification.document_type, classification.topic)

            # 4. Embed / index
            logger.info("   Embedding …")
            all_chunks = []
            for p in pages:
                if p.text_content:
                    chunks = EmbedderService.chunk_text(
                        p.text_content, p.page_number, doc_id, original_name
                    )
                    all_chunks.extend(chunks)
            if all_chunks:
                embedder.embed_and_store(all_chunks)
            doc.status = "indexed"
            await session.commit()
            logger.info("   Indexed %d chunk(s). ✓", len(all_chunks))
            return True

        except Exception as exc:
            logger.error("   FAILED: %s", exc, exc_info=True)
            doc.status = "error"
            doc.error_message = str(exc)
            await session.commit()
            return False


async def main() -> None:
    # Determine docs directory
    if len(sys.argv) > 1:
        docs_dir = Path(sys.argv[1])
    else:
        docs_dir = Path(__file__).resolve().parent / "sample_docs"

    if not docs_dir.is_dir():
        logger.error("Directory not found: %s", docs_dir)
        logger.info("Create a 'sample_docs' folder next to 'backend/' and place files in it.")
        sys.exit(1)

    # Collect supported files
    supported = settings.ALLOWED_EXTENSIONS
    files = sorted(
        f for f in docs_dir.iterdir()
        if f.is_file() and f.suffix.lstrip(".").lower() in supported
    )

    if not files:
        logger.warning("No supported files found in %s", docs_dir)
        sys.exit(0)

    logger.info("Found %d file(s) in %s", len(files), docs_dir)

    # Init
    await init_db()
    embedder = EmbedderService()

    success = 0
    for f in files:
        ok = await seed_file(f, embedder)
        if ok:
            success += 1

    logger.info("═══ Seed complete: %d / %d succeeded. ═══", success, len(files))


if __name__ == "__main__":
    asyncio.run(main())
