"""
RAG Engine — DevOps Knowledge Base
====================================
Searches ChromaDB for relevant DevOps context based on user's question.
Supports: Kubernetes docs, Docker guides, and application log analysis.

Used by llm_engine.py to provide knowledge-grounded answers.
"""

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "devops_knowledge"
TOP_K = 5  # Increased for better DevOps context coverage


# ─── RAG RETRIEVER CLASS ─────────────────────────────────────────────────────

class FAQRetriever:
    """Loads ChromaDB and retrieves relevant DevOps knowledge chunks for a given query."""

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

    def search(self, query: str, top_k: int = TOP_K) -> str:
        """
        Search for relevant DevOps knowledge chunks matching the user's question.
        Returns a formatted string of relevant context to feed to the LLM.
        """
        if not self.vectorstore:
            return ""

        results = self.vectorstore.similarity_search(query, k=top_k)

        if not results:
            return ""

        # Format results as context for the LLM
        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "unknown")
            source_type = doc.metadata.get("type", "document")
            
            # Extract just the filename from the full path
            source_name = os.path.basename(source) if source else "unknown"
            
            context_parts.append(
                f"[Source {i} — {source_type}: {source_name}]:\n{doc.page_content.strip()}"
            )

        context = "\n\n".join(context_parts)
        return context

    def is_ready(self) -> bool:
        """Check if the RAG engine is loaded and ready."""
        return self.vectorstore is not None


# ─── SINGLETON INSTANCE ──────────────────────────────────────────────────────
# Created once when this module is imported, reused across all requests.

faq_retriever = FAQRetriever()
