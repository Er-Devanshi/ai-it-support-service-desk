#!/usr/bin/env python3
"""
Convenience entry point to ingest the IT knowledge base into ChromaDB.
Run:
    python ingest_knowledge_base.py
    python ingest_knowledge_base.py --reset
    python ingest_knowledge_base.py --mock-embeddings
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.rag.ingest import main

if __name__ == "__main__":
    main()
