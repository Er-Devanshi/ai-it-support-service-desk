"""
ServiceDesk-AI Configuration module.
Loads settings from environment variables and provides centralized configuration.
"""

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file from repository root if it exists
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    # Application settings
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS origins
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5500,file://*").split(",")
        if origin.strip()
    ]
    # In development, allow wildcard if configured or if origins contain '*'
    ALLOW_ALL_ORIGINS: bool = "*" in os.getenv("CORS_ORIGINS", "*")

    # LLM Settings (Provider-independent)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    LLM_MODEL: str = os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    
    # Gemini specific
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # OpenAI specific (future support)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Ollama specific (future local support)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'backend' / 'servicedesk.db'}"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "servicedesk-secret-key-change-in-production-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_MINUTES: int = int(os.getenv("JWT_EXPIRY_MINUTES", "120"))

    # RAG & Vector Database settings
    KNOWLEDGE_BASE_DIR: Path = Path(os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "data" / "knowledge_base")))
    CHROMA_PERSIST_DIR: Path = Path(os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db")))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "servicedesk_knowledge_base")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
    RAG_RELEVANCE_THRESHOLD: float = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.30"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "600"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "80"))
    RAG_ENABLED: bool = os.getenv("RAG_ENABLED", "true").lower() in ("true", "1", "yes")

    # Demo / Mock mode override
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")


settings = Settings()
