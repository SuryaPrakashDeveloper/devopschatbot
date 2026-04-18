"""
RAG Engine — DevOps Knowledge Base (v2: Company-Aware)
========================================================
Searches ChromaDB for relevant DevOps context based on user's question.
Supports: Kubernetes docs, Docker guides, and application log analysis.

v2 Changes:
- Intent-based filtered retrieval (debug → runbooks/errors, logs → log chunks)
- Service name extraction from queries (samadhanb, pencil, ssp)
- Confidence scoring (high/medium/low/none)
- Relevance threshold + context capping

Used by llm_engine.py to provide knowledge-grounded answers.
"""

import os
import re
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "devops_knowledge"
TOP_K = 3
MIN_RELEVANCE_SCORE = 0.3

# Known service names (extracted from data directory at startup)
KNOWN_SERVICES = [
    "samadhanb-master", "samadhanb-office", "samadhanb-recon",
    "samadhanb-user-labour", "samadhanb-voting",
    "pencil-compliant-service", "pencil-frontend", "pencil-master-service",
    "pencil-office-service", "pencil-user-service",
    "ssp-sspb-establishment", "ssp-sspb-inspection", "ssp-sspb-master",
    "ssp-sspb-office", "ssp-sspb-registration", "ssp-sspb-return", "ssp-sspb-user",
]

# Short aliases for matching (samadhanb → samadhanb-*)
SERVICE_ALIASES = {
    "samadhanb": "samadhanb",
    "samadhan": "samadhanb",
    "pencil": "pencil",
    "ssp": "ssp-sspb",
    "sspb": "ssp-sspb",
}

# Intent → chunk type filter mapping
INTENT_TYPE_FILTERS = {
    "debugging": ["log_errors", "log_warnings", "log_summary", "documentation"],
    "log_analysis": ["log_errors", "log_warnings", "log_summary", "log_http_errors", "log_endpoints"],
    "explanation": ["documentation"],
    "howto": ["documentation"],
    "command": ["documentation"],
    "general": None,  # No filter — search everything
}


# ─── SERVICE NAME EXTRACTOR ──────────────────────────────────────────────────

def extract_service_from_query(query: str) -> str | None:
    """
    Extract a service/application name from the user's query.
    Returns the service prefix (e.g., 'samadhanb') or None.
    
    Examples:
        "errors in samadhanb" → "samadhanb"
        "ssp office logs" → "ssp-sspb"
        "what is kubernetes" → None
    """
    query_lower = query.lower()

    # Check exact service names first
    for service in KNOWN_SERVICES:
        if service in query_lower:
            return service

    # Check aliases
    for alias, prefix in SERVICE_ALIASES.items():
        if alias in query_lower:
            return prefix

    return None


# ─── RAG RETRIEVER CLASS ─────────────────────────────────────────────────────

class FAQRetriever:
    """Company-aware retriever with intent filtering and confidence scoring."""

    def __init__(self):
        self.vectorstore = None
        self.embeddings = None
        self._load()

    def _load(self):
        """Load embedding model and connect to ChromaDB."""
        db_path = os.path.abspath(CHROMA_DB_DIR)

        if not os.path.exists(db_path):
            print(f"⚠️  ChromaDB not found at: {db_path}")
            print(f"   Run 'python ingest_data.py' first to create the vector database.")
            return

        print(f"🔗 Loading embedding model: {EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        print(f"🔗 Connecting to ChromaDB: {db_path}")
        self.vectorstore = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME,
        )
        
        chunk_count = self.vectorstore._collection.count()
        print(f"✅ RAG Engine ready! ({chunk_count} chunks loaded)")
        print(f"   📚 Knowledge base: Kubernetes, Docker, Application Logs")
        print(f"   🎯 Relevance threshold: {MIN_RELEVANCE_SCORE} | Max chunks: {TOP_K}")
        print(f"   🏢 Known services: {len(KNOWN_SERVICES)} ({', '.join(set(s.split('-')[0] for s in KNOWN_SERVICES))})")

    def search(self, query: str, intent: str = "general", top_k: int = TOP_K) -> tuple[str, str]:
        """
        Company-aware search with intent filtering and confidence scoring.
        
        Args:
            query: User's question
            intent: Query intent from classifier
            top_k: Max results to return
            
        Returns: (context_string, confidence_level)
            - context_string: Formatted context for LLM
            - confidence_level: "high", "medium", "low", or "none"
        """
        if not self.vectorstore:
            return "", "none"

        # --- Build metadata filter ---
        metadata_filter = self._build_filter(query, intent)

        # --- Search with filter ---
        try:
            if metadata_filter:
                results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=top_k, filter=metadata_filter
                )
            else:
                results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=top_k
                )
        except Exception:
            # Fallback: search without filter if filter fails
            try:
                results = self.vectorstore.similarity_search(query, k=top_k)
                results_with_scores = [(doc, 1.0) for doc in results]
            except Exception:
                return "", "none"

        if not results_with_scores:
            return "", "none"

        # --- Filter by relevance score ---
        filtered = [(doc, score) for doc, score in results_with_scores if score >= MIN_RELEVANCE_SCORE]

        if not filtered:
            return "", "none"

        # --- Calculate confidence level ---
        avg_score = sum(s for _, s in filtered) / len(filtered)
        top_score = filtered[0][1] if filtered else 0

        if top_score >= 0.6:
            confidence = "high"
        elif top_score >= 0.4:
            confidence = "medium"
        else:
            confidence = "low"

        # --- Format context (capped at 3000 chars) ---
        context_parts = []
        total_chars = 0
        MAX_CONTEXT_CHARS = 3000

        for i, (doc, score) in enumerate(filtered, 1):
            source = doc.metadata.get("source", "unknown")
            source_type = doc.metadata.get("type", "document")
            service = doc.metadata.get("service", "")
            source_name = os.path.basename(source) if source else "unknown"
            
            service_tag = f" | service: {service}" if service else ""
            chunk_text = (
                f"[Source {i} — {source_type}: {source_name}{service_tag} (relevance: {score:.2f})]:\n"
                f"{doc.page_content.strip()}"
            )
            
            if total_chars + len(chunk_text) > MAX_CONTEXT_CHARS:
                break
            
            context_parts.append(chunk_text)
            total_chars += len(chunk_text)

        context = "\n\n".join(context_parts)
        return context, confidence

    def _build_filter(self, query: str, intent: str) -> dict | None:
        """Build ChromaDB metadata filter based on intent and service name."""
        filters = []

        # --- Filter by chunk type based on intent ---
        type_filter_list = INTENT_TYPE_FILTERS.get(intent)
        if type_filter_list:
            filters.append({"type": {"$in": type_filter_list}})

        # --- Filter by service name if detected in query ---
        service = extract_service_from_query(query)
        if service:
            # Find all matching services (prefix match)
            matching_services = [s for s in KNOWN_SERVICES if s.startswith(service)]
            if matching_services:
                filters.append({"service": {"$in": matching_services}})

        # --- Combine filters ---
        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]
        return {"$and": filters}

    def get_known_services(self) -> list[str]:
        """Return list of known service names for 'not found' suggestions."""
        return KNOWN_SERVICES

    def is_ready(self) -> bool:
        """Check if the RAG engine is loaded and ready."""
        return self.vectorstore is not None


# ─── SINGLETON INSTANCE ──────────────────────────────────────────────────────
faq_retriever = FAQRetriever()
