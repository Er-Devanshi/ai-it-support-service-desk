"""
ServiceDesk-AI — Main FastAPI application entry point.

Autonomous Multi-Agent Assistant for Enterprise IT Operations.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import init_database
from app.routes import health, chat, auth, tickets, approvals, actions, audit, rag
from app.utils.logger import logger
from app.services.nlp.bm25 import BM25Index

# Global flag to track if BM25 index initialization failed
_index_build_failed = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and startup checks."""
    logger.info("Starting ServiceDesk-AI backend...")
    init_database()
    
    # Initialize BM25 index from knowledge base if missing or empty
    _initialize_bm25_index()
    
    yield
    logger.info("Shutting down ServiceDesk-AI backend.")


def _initialize_bm25_index():
    """Build BM25 index from knowledge base documents if missing or empty."""
    from app.services.rag.ingest import ingest_knowledge_base
    from app.services.nlp.retriever import BM25Retriever
    
    global _index_build_failed
    _index_build_failed = False
    
    try:
        retriever = BM25Retriever(index_path=settings.BM25_INDEX_PATH)
        
        # Check if index exists and has documents
        if retriever.index and retriever.index.total_docs > 0:
            logger.info(f"BM25 index loaded: {retriever.index.total_docs} documents ready")
            return
        
        # Index is missing or empty - rebuild from knowledge base
        logger.info(f"Building BM25 index from knowledge base at {settings.KNOWLEDGE_BASE_DIR}...")
        result = ingest_knowledge_base(directory=settings.KNOWLEDGE_BASE_DIR, reset=False)
        if result.get("status") == "success":
            logger.info(f"✓ BM25 index built successfully: {result.get('chunks_indexed', '?')} chunks indexed")
        else:
            logger.warning(f"Ingestion warning: {result.get('message', 'Unknown error')}")
            _index_build_failed = True
    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}")
        _index_build_failed = True
        # Create empty index so server doesn't crash
        try:
            retriever = BM25Retriever(index_path=settings.BM25_INDEX_PATH)
            if not retriever.index:
                retriever.index = BM25Index()
            retriever.index.finalize()
            retriever.save_index()
            logger.warning("Empty BM25 index created - RAG will return no results until indexed manually")
        except Exception as e2:
            logger.error(f"Failed to create empty index: {e2}")


app = FastAPI(
    title="ServiceDesk-AI",
    description=(
        "Autonomous Multi-Agent AI Assistant for Enterprise IT Operations. "
        "Provides conversational support, AI triage & prioritization, LangGraph orchestration, "
        "RAG integration contracts, simulated IT actions, human-in-the-loop approvals, and RBAC."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
allow_origins = ["*"] if settings.ALLOW_ALL_ORIGINS else settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers Registration
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(actions.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(rag.router, prefix="/api")

# ---------------------------------------------------------------------------
# Static Frontend Serving
# ---------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    css_dir = frontend_dir / "css"
    js_dir = frontend_dir / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/", tags=["Frontend"])
    def serve_frontend():
        """Serve the ServiceDesk-AI dashboard interface."""
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"service": "ServiceDesk-AI", "api_docs": "/docs"}
