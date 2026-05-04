"""
config.py — Environment and configuration management.
"""

import os
from dotenv import load_dotenv

# Load .env from the orchestrator root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings:
    """Centralised application settings loaded from environment."""

    GEMINI_API_KEY_BLUE: str = os.getenv("GEMINI_API_KEY_BLUE", "")
    GEMINI_API_KEY_RED: str = os.getenv("GEMINI_API_KEY_RED", "")

    ARENA_URL: str = os.getenv("ARENA_URL", "http://localhost:8080")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    FALLBACK_MODELS: list = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]


settings = Settings()
