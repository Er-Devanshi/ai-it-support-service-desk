"""
Document ingestion module for ServiceDesk-AI RAG pipeline.

Supports:
- Plain text (.txt)
- Markdown (.md)
- PDF documentation (.pdf) via pypdf
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.config import settings
from app.utils.logger import logger

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class LoadedDocument(BaseModel):
    """Raw document content and provenance metadata before chunking."""
    file_path: str = Field(description="Full or relative filesystem path")
    file_name: str = Field(description="Base filename with extension")
    file_type: str = Field(description="File extension type: 'txt', 'md', 'pdf'")
    title: str = Field(description="Extracted or inferred document title")
    content: str = Field(description="Extracted text content")
    category: Optional[str] = Field(default="general", description="Inferred IT domain category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")


def _infer_category_from_text(text: str, default: str = "general") -> str:
    """Infer common IT category from content headers or keywords."""
    lower = text[:500].lower()
    if any(k in lower for k in ["vpn", "wi-fi", "wifi", "network", "router", "dhcp", "dns", "ethernet"]):
        return "network"
    if any(k in lower for k in ["password", "account", "login", "unlock", "mfa", "credentials"]):
        return "account"
    if any(k in lower for k in ["printer", "laptop", "monitor", "dock", "hardware", "keyboard"]):
        return "hardware"
    if any(k in lower for k in ["email", "outlook", "sync", "mailbox", "smtp"]):
        return "email"
    if any(k in lower for k in ["software", "install", "license", "application", "browser"]):
        return "software"
    if any(k in lower for k in ["security", "phishing", "malware", "incident", "breach"]):
        return "security"
    return default


def _extract_title(content: str, file_name: str) -> str:
    """Extract document title from first Markdown # header or capitalize filename."""
    lines = content.splitlines()
    for line in lines[:10]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("TITLE:"):
            return stripped[6:].strip()
        if "—" in stripped and stripped.lower().startswith("faq"):
            return stripped.strip("- =")
    # Fallback to sanitized filename
    name_stem = Path(file_name).stem.replace("_", " ").replace("-", " ")
    return name_stem.title()


def load_file(file_path: Path) -> LoadedDocument:
    """Load a single document from filesystem (txt, md, or pdf)."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Document file not found at: {file_path}")

    suffix = file_path.suffix.lower()
    file_name = file_path.name

    if suffix in [".txt", ".text"]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        file_type = "txt"
    elif suffix in [".md", ".markdown"]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        file_type = "md"
    elif suffix == ".pdf":
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf is required to load PDF documents but is not installed.")
        reader = pypdf.PdfReader(str(file_path))
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
        content = "\n\n".join(text_parts)
        file_type = "pdf"
    else:
        # Fallback text reading for other extension types
        content = file_path.read_text(encoding="utf-8", errors="replace")
        file_type = suffix.lstrip(".") or "txt"

    title = _extract_title(content, file_name)
    category = _infer_category_from_text(content)

    return LoadedDocument(
        file_path=str(file_path),
        file_name=file_name,
        file_type=file_type,
        title=title,
        content=content,
        category=category,
        metadata={
            "size_bytes": file_path.stat().st_size,
            "modified_time": file_path.stat().st_mtime,
        },
    )


def load_knowledge_base_dir(directory: Optional[Path] = None) -> List[LoadedDocument]:
    """
    Load all supported IT documents from the knowledge base directory.
    Supported extensions: .txt, .md, .pdf
    """
    kb_dir = directory or settings.KNOWLEDGE_BASE_DIR
    if not kb_dir.exists():
        logger.warning(f"Knowledge base directory does not exist: {kb_dir}")
        return []

    documents: List[LoadedDocument] = []
    supported_extensions = {".txt", ".md", ".pdf"}

    for path in sorted(kb_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in supported_extensions:
            # Skip hidden files or temp files
            if path.name.startswith(".") or path.name.startswith("~"):
                continue
            try:
                doc = load_file(path)
                if doc.content.strip():
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to load document {path}: {e}")

    logger.info(f"Loaded {len(documents)} document(s) from {kb_dir}")
    return documents
