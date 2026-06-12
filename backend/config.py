"""
Application configuration.

Loads settings from environment variables / .env file with sensible defaults.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Also try .env inside backend/
    load_dotenv(Path(__file__).resolve().parent / ".env")


class Settings:
    """Centralised application settings populated from environment variables."""

    # ── API Keys ──────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    API_KEY: str = os.getenv("API_KEY", "")  # empty ⇒ auth disabled

    # ── Paths ─────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    CHROMA_DIR: Path = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db")))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{BASE_DIR / 'docintel.db'}",
    )

    # ── Upload constraints ────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "50"))
    ALLOWED_EXTENSIONS: set[str] = set(
        os.getenv(
            "ALLOWED_EXTENSIONS",
            "pdf,png,jpg,jpeg,tiff,tif,bmp,webp",
        ).split(",")
    )

    # ── CORS / Rate limiting ─────────────────────────────────────────────
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080",
    ).split(",")
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "60/minute")

    # ── Embedding / LLM ──────────────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    # ── Derived helpers ───────────────────────────────────────────────────
    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()

# Ensure required directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
