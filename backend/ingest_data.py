"""
DevOps Data Ingestion Script
==============================
Reads DevOps data → Creates vector embeddings → Stores in ChromaDB

Supports:
  - PDF documents (Kubernetes guides, Docker tutorials)
  - Application log files (.log, .txt with log content)

Usage:
    cd backend
    python ingest_data.py

Run this once. Run again if your data files change.
"""

import os
import sys
import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# ─── CONFIG ───────────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Devops DATA")
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight, runs locally
COLLECTION_NAME = "devops_knowledge"

# Chunk settings — tuned for technical documentation & logs
PDF_CHUNK_SIZE = 800       # Larger chunks for documentation
PDF_CHUNK_OVERLAP = 100    # Good overlap for technical content
LOG_CHUNK_SIZE = 1500      # Larger chunks for logs (keep context together)
LOG_CHUNK_OVERLAP = 200    # More overlap for log continuity

# Max lines to ingest per log file (to avoid memory issues with huge logs)
MAX_LOG_LINES = 2000


# ─── STEP 1: LOAD PDF DOCUMENTS ─────────────────────────────────────────────

def load_pdfs(data_dir: str) -> list:
    """Load all PDF files from the data directory."""
    all_pages = []
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"   ⚠️ No PDF files found in {data_dir}")
        return all_pages
    
    for pdf_path in pdf_files:
        print(f"   📄 Loading: {pdf_path.name}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            
            # Add metadata
            for page in pages:
                page.metadata["source"] = str(pdf_path)
                page.metadata["type"] = "documentation"
                page.metadata["filename"] = pdf_path.name
            
            all_pages.extend(pages)
            print(f"      ✅ {len(pages)} page(s) loaded")
        except Exception as e:
            print(f"      ❌ Error loading {pdf_path.name}: {e}")
    
    return all_pages


# ─── STEP 2: LOAD APPLICATION LOG FILES ──────────────────────────────────────

def load_log_files(data_dir: str) -> list:
    """Load application log files from the data directory."""
    all_docs = []
    log_extensions = [".log", ".log.txt"]
    
    log_files = []
    for ext in ["*.log", "*.log.txt"]:
        log_files.extend(Path(data_dir).glob(ext))
    
    # Also grab .txt files that look like logs
    for txt_file in Path(data_dir).glob("*.txt"):
        if txt_file.name not in [f.name for f in log_files]:
            log_files.append(txt_file)
    
    if not log_files:
        print(f"   ⚠️ No log files found in {data_dir}")
        return all_docs
    
    for log_path in log_files:
        print(f"   📋 Loading: {log_path.name} ({log_path.stat().st_size / 1024:.0f} KB)")
        try:
            # Extract service name from filename
            service_name = extract_service_name(log_path.name)
            
            # Read the log file with a line limit
            lines = []
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if i >= MAX_LOG_LINES:
                        break
                    lines.append(line)
            
            # Create a summary document about this service's logs
            log_summary = analyze_log_content(lines, service_name, log_path.name)
            all_docs.append(log_summary)
            
            # Also create chunks of interesting log segments (errors, warnings, key events)
            interesting_chunks = extract_interesting_log_segments(lines, service_name, log_path.name)
            all_docs.extend(interesting_chunks)
            
            total = 1 + len(interesting_chunks)
            print(f"      ✅ Created {total} knowledge chunk(s)")
        except Exception as e:
            print(f"      ❌ Error loading {log_path.name}: {e}")
    
    return all_docs


def extract_service_name(filename: str) -> str:
    """Extract the service/pod name from the log filename."""
    # Remove common extensions
    name = filename.replace(".log.txt", "").replace(".log", "").replace(".txt", "")
    return name


def analyze_log_content(lines: list, service_name: str, filename: str) -> Document:
    """Create a summary document about the log file's content."""
    total_lines = len(lines)
    
    # Count log levels
    error_count = sum(1 for l in lines if "ERROR" in l.upper() or "EXCEPTION" in l.upper())
    warn_count = sum(1 for l in lines if "WARN" in l.upper())
    info_count = sum(1 for l in lines if "INFO" in l.upper())
    debug_count = sum(1 for l in lines if "DEBUG" in l.upper())
    
    # Count HTTP status codes
    http_200 = sum(1 for l in lines if '" 200 ' in l or "200 OK" in l)
    http_4xx = sum(1 for l in lines if '" 4' in l and ('400 ' in l or '401 ' in l or '403 ' in l or '404 ' in l))
    http_5xx = sum(1 for l in lines if '" 5' in l and ('500 ' in l or '502 ' in l or '503 ' in l))
    
    # Detect log type
    is_nginx = any("nginx" in l.lower() for l in lines[:5])
    is_spring = any("springframework" in l or "DispatcherServlet" in l for l in lines[:50])
    
    log_type = "nginx/web server" if is_nginx else "Spring Boot/Java" if is_spring else "application"
    
    # Get time range
    first_timestamp = ""
    last_timestamp = ""
    for line in lines[:5]:
        if line.strip():
            first_timestamp = line[:30].strip()
            break
    for line in reversed(lines[-5:]):
        if line.strip():
            last_timestamp = line[:30].strip()
            break
    
    # Build summary
    summary = f"""Service/Pod Log Summary: {service_name}
Log File: {filename}
Log Type: {log_type}
Total Lines Analyzed: {total_lines}
Time Range: {first_timestamp} to {last_timestamp}

Log Level Distribution:
- ERROR/EXCEPTION: {error_count}
- WARN: {warn_count}
- INFO: {info_count}
- DEBUG: {debug_count}

HTTP Status Summary:
- 2xx Success: {http_200}
- 4xx Client Errors: {http_4xx}
- 5xx Server Errors: {http_5xx}

Service Health: {"🔴 CRITICAL - Errors detected!" if error_count > 0 else "🟡 WARNINGS present" if warn_count > 0 else "🟢 Healthy - No errors"}
"""
    
    return Document(
        page_content=summary,
        metadata={
            "source": filename,
            "type": "log_summary",
            "service": service_name,
            "error_count": error_count,
            "warn_count": warn_count,
        }
    )


def extract_interesting_log_segments(lines: list, service_name: str, filename: str) -> list:
    """Extract interesting segments from logs (errors, warnings, key patterns)."""
    docs = []
    
    # Extract ERROR and EXCEPTION lines with surrounding context
    error_lines = []
    for i, line in enumerate(lines):
        if "ERROR" in line.upper() or "EXCEPTION" in line.upper() or "FATAL" in line.upper():
            # Get context: 2 lines before and 3 lines after
            start = max(0, i - 2)
            end = min(len(lines), i + 4)
            segment = "".join(lines[start:end])
            error_lines.append(segment)
    
    if error_lines:
        # Combine error segments (limit to first 10)
        error_content = f"Error Log Segments from {service_name} ({filename}):\n\n"
        error_content += "\n---\n".join(error_lines[:10])
        docs.append(Document(
            page_content=error_content,
            metadata={"source": filename, "type": "log_errors", "service": service_name}
        ))
    
    # Extract WARNING lines
    warn_lines = []
    for i, line in enumerate(lines):
        if "WARN" in line.upper() and "ERROR" not in line.upper():
            warn_lines.append(line.strip())
    
    if warn_lines:
        warn_content = f"Warning Log Lines from {service_name} ({filename}):\n\n"
        warn_content += "\n".join(warn_lines[:20])
        docs.append(Document(
            page_content=warn_content,
            metadata={"source": filename, "type": "log_warnings", "service": service_name}
        ))
    
    # Extract HTTP 4xx/5xx error patterns
    http_errors = []
    for line in lines:
        if any(code in line for code in ['" 400 ', '" 401 ', '" 403 ', '" 404 ', '" 500 ', '" 502 ', '" 503 ']):
            http_errors.append(line.strip())
    
    if http_errors:
        http_content = f"HTTP Error Responses from {service_name} ({filename}):\n\n"
        http_content += "\n".join(http_errors[:20])
        docs.append(Document(
            page_content=http_content,
            metadata={"source": filename, "type": "log_http_errors", "service": service_name}
        ))
    
    # Extract API endpoint patterns (first 500 unique endpoints)
    endpoints = set()
    for line in lines:
        if "GET " in line or "POST " in line or "PUT " in line or "DELETE " in line:
            # Extract the HTTP method and path
            for method in ["GET ", "POST ", "PUT ", "DELETE ", "OPTIONS ", "PATCH "]:
                if method in line:
                    start_idx = line.index(method)
                    segment = line[start_idx:start_idx+150].split('"')[0].split(" HTTP")[0]
                    if segment:
                        endpoints.add(segment.strip())
    
    if endpoints:
        endpoint_content = f"API Endpoints detected in {service_name} ({filename}):\n\n"
        endpoint_content += "\n".join(sorted(list(endpoints))[:50])
        docs.append(Document(
            page_content=endpoint_content,
            metadata={"source": filename, "type": "log_endpoints", "service": service_name}
        ))
    
    return docs


# ─── STEP 3: SPLIT INTO CHUNKS ──────────────────────────────────────────────

def split_documents(pages: list, chunk_size: int, chunk_overlap: int) -> list:
    """Split documents into smaller chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = splitter.split_documents(pages)
    return chunks


# ─── STEP 4: CREATE EMBEDDINGS & STORE IN CHROMADB ──────────────────────────

def create_vector_store(all_chunks: list):
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
    print(f"   Embedding {len(all_chunks)} chunks... (this may take a minute)")
    
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME,
    )
    
    print(f"   ✅ Vector database created successfully!")
    print(f"   📁 Stored at: {os.path.abspath(CHROMA_DB_DIR)}")
    
    return vectorstore


# ─── STEP 5: VERIFY ─────────────────────────────────────────────────────────

def verify_store(vectorstore):
    """Quick test — search for something to verify it works."""
    print(f"\n🔍 Quick verification tests...")
    
    test_queries = [
        "What is Kubernetes?",
        "How to check pod status?",
        "Show me error logs",
        "Docker container commands",
    ]
    
    for query in test_queries:
        results = vectorstore.similarity_search(query, k=2)
        print(f"\n   Query: \"{query}\"")
        print(f"   Found {len(results)} results:")
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "unknown")
            source_name = os.path.basename(source) if source else "unknown"
            doc_type = doc.metadata.get("type", "document")
            preview = doc.page_content[:120].replace('\n', ' ')
            print(f"   📎 [{doc_type}] {source_name}: {preview}...")
    
    print(f"\n✅ Everything is working! Knowledge base is ready for DevOps queries.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  🚀 DevOps Chatbot — Data Ingestion Script")
    print("  📚 Sources: PDFs + Application Logs")
    print("=" * 70)
    
    data_dir = os.path.abspath(DATA_DIR)
    
    if not os.path.exists(data_dir):
        print(f"\n❌ Data directory not found: {data_dir}")
        print(f"   Please create the directory and add your DevOps data files.")
        sys.exit(1)
    
    all_chunks = []
    
    # Step 1: Load PDFs (Kubernetes guide, Docker tutorial)
    print(f"\n📄 PHASE 1: Loading PDF Documents...")
    print(f"   Directory: {data_dir}")
    pdf_pages = load_pdfs(data_dir)
    if pdf_pages:
        pdf_chunks = split_documents(pdf_pages, PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP)
        all_chunks.extend(pdf_chunks)
        print(f"   📊 Total PDF chunks: {len(pdf_chunks)}")
    
    # Step 2: Load Log Files
    print(f"\n📋 PHASE 2: Loading Application Logs...")
    log_docs = load_log_files(data_dir)
    if log_docs:
        # Log docs are already pre-chunked by the analysis
        # But split any large ones further
        log_chunks = split_documents(log_docs, LOG_CHUNK_SIZE, LOG_CHUNK_OVERLAP)
        all_chunks.extend(log_chunks)
        print(f"   📊 Total log chunks: {len(log_chunks)}")
    
    if not all_chunks:
        print(f"\n❌ No data was loaded! Please check your data directory.")
        sys.exit(1)
    
    print(f"\n{'=' * 70}")
    print(f"   📊 TOTAL CHUNKS TO EMBED: {len(all_chunks)}")
    print(f"{'=' * 70}")
    
    # Step 3: Create embeddings & store
    vectorstore = create_vector_store(all_chunks)
    
    # Step 4: Verify
    verify_store(vectorstore)
    
    print("\n" + "=" * 70)
    print("  ✅ DONE! DevOps knowledge base is ready.")
    print("  🧠 The chatbot can now answer questions about:")
    print("     - Kubernetes & Docker (from PDF guides)")
    print("     - Your application logs & service health")
    print("     - Error patterns & troubleshooting")
    print("=" * 70)
