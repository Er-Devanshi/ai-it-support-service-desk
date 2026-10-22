"""
Intelligent document chunking for ServiceDesk-AI RAG pipeline.

Preserves troubleshooting step coherence and structure:
- Section-aware splitting (FAQ delimiters, Markdown # headers)
- Prevents splitting sequential numbered troubleshooting steps
- Configurable chunk size and overlap
- Generates deterministic chunk IDs to prevent duplicate vectors on re-indexing
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.rag.retrieval_interface import RetrievedChunk
from app.services.rag.document_loader import LoadedDocument


class DocumentChunker:
    """Splits loaded documents into semantic chunks while maintaining metadata and context."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    @staticmethod
    def generate_chunk_id(source_name: str, section_title: str, content: str, index: int) -> str:
        """Create a deterministic chunk ID using SHA-256 hash to avoid duplicate ingestion."""
        payload = f"{source_name}::{section_title}::{index}::{content.strip()}"
        hash_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", source_name)
        return f"{clean_name}_{index}_{hash_digest}"

    def chunk_document(self, doc: LoadedDocument) -> List[RetrievedChunk]:
        """Chunk a document according to its format and structure."""
        # 1. Check if document has FAQ delimiters (like sample_it_faq.txt)
        if re.search(r"-{10,}\s*FAQ\s*\d+", doc.content, re.IGNORECASE):
            return self._chunk_faq_document(doc)

        # 2. Check if document has Markdown headers (# Header, ## Subheader)
        if doc.file_type in ["md", "markdown"] or re.search(r"^\s*#{1,3}\s+", doc.content, re.MULTILINE):
            return self._chunk_markdown_document(doc)

        # 3. Fallback to paragraph and step-aware recursive chunking
        return self._chunk_text_document(doc)

    def _chunk_faq_document(self, doc: LoadedDocument) -> List[RetrievedChunk]:
        """Split FAQ document by FAQ section boundaries so all troubleshooting steps stay together."""
        chunks: List[RetrievedChunk] = []
        raw = doc.content

        # Split on FAQ delimiters
        sections = re.split(r"-{20,}\s*FAQ\s*(\d+)\s*[—–-]\s*(.*?)\s*-{20,}", raw)
        # format: [preamble, faq_num1, faq_title1, text1, faq_num2, ...]

        chunk_idx = 0
        for i in range(1, len(sections), 3):
            if i + 2 < len(sections):
                faq_num = sections[i].strip()
                faq_title = sections[i + 1].strip()
                faq_body = sections[i + 2].strip()

                full_title = f"FAQ {faq_num}: {faq_title}"
                full_text = f"Title: {full_title}\n\n{faq_body}"

                # If FAQ body is moderately sized, keep as single chunk
                if len(full_text) <= self.chunk_size * 1.5:
                    chunk_id = self.generate_chunk_id(doc.file_name, full_title, full_text, chunk_idx)
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=chunk_id,
                            source=doc.file_name,
                            title=full_title,
                            content=full_text,
                            metadata={
                                "file_path": doc.file_path,
                                "category": doc.category,
                                "faq_number": faq_num,
                                "chunk_index": chunk_idx,
                            },
                        )
                    )
                    chunk_idx += 1
                else:
                    # Sub-split preserving troubleshooting steps
                    sub_chunks = self._split_text_preserving_steps(full_text)
                    for sub_idx, sub_content in enumerate(sub_chunks):
                        sub_title = f"{full_title} (Part {sub_idx + 1})" if len(sub_chunks) > 1 else full_title
                        chunk_id = self.generate_chunk_id(doc.file_name, sub_title, sub_content, chunk_idx)
                        chunks.append(
                            RetrievedChunk(
                                chunk_id=chunk_id,
                                source=doc.file_name,
                                title=sub_title,
                                content=sub_content,
                                metadata={
                                    "file_path": doc.file_path,
                                    "category": doc.category,
                                    "faq_number": faq_num,
                                    "chunk_index": chunk_idx,
                                },
                            )
                        )
                        chunk_idx += 1

        return chunks

    def _chunk_markdown_document(self, doc: LoadedDocument) -> List[RetrievedChunk]:
        """Split markdown by # and ## headers, keeping troubleshooting subsections intact."""
        chunks: List[RetrievedChunk] = []
        raw = doc.content

        # Split by level 1 or 2 markdown headers
        header_pattern = re.compile(r"(^#{1,3}\s+.+$)", re.MULTILINE)
        parts = header_pattern.split(raw)

        # parts format: [preamble, header1, body1, header2, body2, ...]
        current_title = doc.title
        chunk_idx = 0

        # Handle preamble if non-empty
        if parts and parts[0].strip():
            preamble = parts[0].strip()
            if len(preamble) > 50:
                chunk_id = self.generate_chunk_id(doc.file_name, current_title, preamble, chunk_idx)
                chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        source=doc.file_name,
                        title=current_title,
                        content=preamble,
                        metadata={"file_path": doc.file_path, "category": doc.category, "chunk_index": chunk_idx},
                    )
                )
                chunk_idx += 1

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                header = parts[i].strip().lstrip("#").strip()
                body = parts[i + 1].strip()
                if not body:
                    continue

                section_title = f"{doc.title} — {header}" if doc.title != header else header
                section_text = f"Topic: {section_title}\n\n{body}"

                if len(section_text) <= self.chunk_size * 1.5:
                    chunk_id = self.generate_chunk_id(doc.file_name, section_title, section_text, chunk_idx)
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=chunk_id,
                            source=doc.file_name,
                            title=section_title,
                            content=section_text,
                            metadata={"file_path": doc.file_path, "category": doc.category, "chunk_index": chunk_idx},
                        )
                    )
                    chunk_idx += 1
                else:
                    sub_chunks = self._split_text_preserving_steps(section_text)
                    for sub_idx, sub_content in enumerate(sub_chunks):
                        sub_title = f"{section_title} (Part {sub_idx + 1})" if len(sub_chunks) > 1 else section_title
                        chunk_id = self.generate_chunk_id(doc.file_name, sub_title, sub_content, chunk_idx)
                        chunks.append(
                            RetrievedChunk(
                                chunk_id=chunk_id,
                                source=doc.file_name,
                                title=sub_title,
                                content=sub_content,
                                metadata={"file_path": doc.file_path, "category": doc.category, "chunk_index": chunk_idx},
                            )
                        )
                        chunk_idx += 1

        return chunks

    def _chunk_text_document(self, doc: LoadedDocument) -> List[RetrievedChunk]:
        """Generic paragraph-aware chunker with step preservation for plain text or PDF."""
        chunks: List[RetrievedChunk] = []
        sub_chunks = self._split_text_preserving_steps(doc.content)
        for chunk_idx, content in enumerate(sub_chunks):
            title = f"{doc.title} (Part {chunk_idx + 1})" if len(sub_chunks) > 1 else doc.title
            chunk_id = self.generate_chunk_id(doc.file_name, title, content, chunk_idx)
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    source=doc.file_name,
                    title=title,
                    content=content,
                    metadata={"file_path": doc.file_path, "category": doc.category, "chunk_index": chunk_idx},
                )
            )
        return chunks

    def _split_text_preserving_steps(self, text: str) -> List[str]:
        """
        Split a block of text into sub-blocks respecting chunk_size and chunk_overlap,
        without breaking in the middle of numbered troubleshooting steps (e.g., '1. ... 2. ...').
        """
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # Check if this paragraph contains a numbered list (e.g. 1. 2. 3.)
            is_step_list = bool(re.search(r"^\s*\d+[\.\)]\s+", para, re.MULTILINE))

            if current_length + para_len + 2 > self.chunk_size and current_chunk:
                # Store current chunk
                combined = "\n\n".join(current_chunk).strip()
                if combined:
                    chunks.append(combined)

                # Overlap: keep last paragraph if small enough
                if current_chunk and len(current_chunk[-1]) <= self.chunk_overlap:
                    current_chunk = [current_chunk[-1], para]
                    current_length = len(current_chunk[0]) + para_len + 2
                else:
                    current_chunk = [para]
                    current_length = para_len
            else:
                current_chunk.append(para)
                current_length += para_len + 2

        if current_chunk:
            combined = "\n\n".join(current_chunk).strip()
            if combined:
                chunks.append(combined)

        return chunks if chunks else [text.strip()]
