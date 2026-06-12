"""
SQLAlchemy async models and database initialisation for SQLite.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings

import logging

logger = logging.getLogger(__name__)

# ── Engine & Session ──────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Status enum values ────────────────────────────────────────────────────────

DOCUMENT_STATUSES = (
    "uploading",
    "parsing",
    "classifying",
    "indexing",
    "indexed",
    "error",
)


# ── Document model ────────────────────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: str = Column(String(512), nullable=False)
    original_filename: str = Column(String(512), nullable=False)
    status: str = Column(
        String(20),
        nullable=False,
        default="uploading",
    )
    classification: dict[str, Any] | None = Column(JSON, nullable=True)
    page_count: int | None = Column(Integer, nullable=True)
    error_message: str | None = Column(Text, nullable=True)
    uploaded_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    file_size: int | None = Column(BigInteger, nullable=True)

    # Relationship
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.original_filename,
            "status": self.status,
            "classification": self.classification,
            "page_count": self.page_count,
            "error_message": self.error_message,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "file_size": self.file_size,
        }


# ── Page model ────────────────────────────────────────────────────────────────

class Page(Base):
    __tablename__ = "pages"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    document_id: str = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    page_number: int = Column(Integer, nullable=False)
    text_content: str | None = Column(Text, nullable=True)
    has_tables: bool = Column(Boolean, default=False)
    thumbnail_path: str | None = Column(String(1024), nullable=True)
    full_image_path: str | None = Column(String(1024), nullable=True)

    document = relationship("Document", back_populates="pages")


# ── Database init ─────────────────────────────────────────────────────────────

async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


async def get_session() -> AsyncSession:
    """Dependency that yields an async session."""
    async with async_session_factory() as session:
        yield session  # type: ignore[misc]
