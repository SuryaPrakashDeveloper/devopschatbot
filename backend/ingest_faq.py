"""
⚠️  DEPRECATED — DO NOT USE THIS SCRIPT
=========================================
This script writes to the OLD 'faq_hudco' collection.
The chatbot now uses the 'devops_knowledge' collection.

Use 'python ingest_data.py' instead.

Running this script will NOT break anything, but the data it writes
will NOT be used by the chatbot (different collection name).
"""

import sys
print("❌ DEPRECATED: This script is no longer used.")
print("   Use 'python ingest_data.py' instead.")
print("   The chatbot reads from collection 'devops_knowledge', not 'faq_hudco'.")
sys.exit(1)

import os
import sys
import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ─── CONFIG ───────────────────────────────────────────────────────────────────

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "FAQ-hudco.pdf")
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight, runs locally

# Chunk settings — tuned for structured Q&A
CHUNK_SIZE = 500       # characters per chunk (keeps Q&A pairs together)
CHUNK_OVERLAP = 50     # overlap to avoid cutting Q&A at boundaries


# ─── STEP 1: LOAD PDF ────────────────────────────────────────────────────────

def load_pdf(pdf_path: str):
    """Load and extract text from PDF."""
    pdf_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    print(f"📄 Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"   ✅ Loaded {len(pages)} page(s)")
    
    # Show a preview of what was extracted
    for i, page in enumerate(pages):
        preview = page.page_content[:200].replace('\n', ' ')
        print(f"   📃 Page {i+1} preview: {preview}...")
    
    return pages


# ─── STEP 2: SPLIT INTO CHUNKS ───────────────────────────────────────────────

def split_into_chunks(pages):
    """Split pages into smaller chunks for embedding."""
    print(f"\n✂️  Splitting into chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],  # Split at paragraph/sentence boundaries
    )
    
    chunks = splitter.split_documents(pages)
    print(f"   ✅ Created {len(chunks)} chunks")
    
    # Show first 3 chunks as preview
    for i, chunk in enumerate(chunks[:3]):
        preview = chunk.page_content[:150].replace('\n', ' ')
        print(f"   📌 Chunk {i+1}: {preview}...")
    
    return chunks


# ─── STEP 3: CREATE EMBEDDINGS & STORE IN CHROMADB ───────────────────────────

def create_vector_store(chunks):
    """Create embeddings and store in ChromaDB."""
    
    # Initialize embedding model (downloads on first run, ~90MB)
    print(f"\n🧠 Loading embedding model: {EMBEDDING_MODEL}")
    print(f"   (First run will download the model, ~90MB. Please wait...)")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print(f"   ✅ Embedding model loaded")
    
    # Clear old database if it exists (fresh re-index)
    if os.path.exists(CHROMA_DB_DIR):
        print(f"\n🗑️  Clearing old vector database...")
        shutil.rmtree(CHROMA_DB_DIR)
    
    # Create ChromaDB and store embeddings
    print(f"\n💾 Creating vector database at: {CHROMA_DB_DIR}")
    print(f"   Embedding {len(chunks)} chunks... (this may take a minute)")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name="faq_hudco",
    )
    
    print(f"   ✅ Vector database created successfully!")
    print(f"   📁 Stored at: {os.path.abspath(CHROMA_DB_DIR)}")
    
    return vectorstore


# ─── STEP 4: VERIFY ──────────────────────────────────────────────────────────

def verify_store(vectorstore):
    """Quick test — search for something to verify it works."""
    print(f"\n🔍 Quick verification test...")
    
    test_query = "What is HUDCO?"
    results = vectorstore.similarity_search(test_query, k=3)
    
    print(f"   Query: \"{test_query}\"")
    print(f"   Found {len(results)} results:")
    for i, doc in enumerate(results):
        preview = doc.page_content[:150].replace('\n', ' ')
        print(f"   📎 Result {i+1}: {preview}...")
    
    print(f"\n✅ Everything is working! Vector database is ready.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  FAQ Ingestion Script — HUDCO Chatbot")
    print("=" * 60)
    
    # Step 1: Load PDF
    pages = load_pdf(PDF_PATH)
    
    # Step 2: Split into chunks
    chunks = split_into_chunks(pages)
    
    # Step 3: Create embeddings & store
    vectorstore = create_vector_store(chunks)
    
    # Step 4: Verify
    verify_store(vectorstore)
    
    print("\n" + "=" * 60)
    print("  ✅ DONE! You can now use the RAG pipeline.")
    print("=" * 60)
