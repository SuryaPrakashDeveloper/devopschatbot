# DevOps Chatbot — Complete Project Documentation

> **Project Name:** DevOps Chatbot  
> **Last Updated:** 15 April 2026  
> **Project Location:** `d:\New folder\devopschatbot\`  
> **Repository:** SuryaPrakashDeveloper/devopschatbot  
> **Status:** Phase 1 — Foundation Built | Transforming to DevOps Chatbot

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement & Why This Chatbot](#2-problem-statement--why-this-chatbot)
3. [Architecture & Tech Stack](#3-architecture--tech-stack)
4. [Project Folder Structure](#4-project-folder-structure)
5. [Backend — Complete Details](#5-backend--complete-details)
6. [Frontend — Complete Details](#6-frontend--complete-details)
7. [Kubernetes Integration — Core Feature](#7-kubernetes-integration--core-feature)
8. [RAG Pipeline — Knowledge Base](#8-rag-pipeline--knowledge-base)
9. [Feature Roadmap & Phases](#9-feature-roadmap--phases)
10. [API Endpoints Reference](#10-api-endpoints-reference)
11. [How to Run the Project](#11-how-to-run-the-project)
12. [Configuration Reference](#12-configuration-reference)
13. [Security & Access Control](#13-security--access-control)
14. [Deployment Guide](#14-deployment-guide)
15. [Troubleshooting & Known Issues](#15-troubleshooting--known-issues)
16. [Decisions Made & Why](#16-decisions-made--why)
17. [Future Enhancements](#17-future-enhancements)

---

## 1. Project Overview

### What is DevOps Chatbot?

DevOps Chatbot is an **AI-powered conversational assistant** designed for **DevOps engineers, developers, and SREs** to interact with their infrastructure using **natural language** instead of complex CLI commands.

Instead of running:
```bash
kubectl get pods -n production --field-selector=status.phase!=Running
```

A developer simply asks:
```
"Are there any crashed pods in production?"
```

The chatbot understands the intent, queries the live Kubernetes cluster, and responds with a **human-friendly, formatted answer**.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **🗣️ Natural Language Interface** | Ask questions in plain English — no need to memorize kubectl commands |
| **📡 Live Cluster Monitoring** | Real-time pod, node, deployment, and service status from Kubernetes clusters |
| **📚 DevOps Knowledge Base** | RAG-powered answers from your team's runbooks, SOPs, and troubleshooting guides |
| **💬 Conversation Memory** | Remembers context within a session — ask follow-up questions naturally |
| **🔄 Multi-Cluster Support** | Monitor DC (Data Center) and DR (Disaster Recovery) clusters from one interface |
| **🤖 AI-Powered Intelligence** | LLM decides what information to fetch and formats it for humans |

### Who Is This For?

| User | How It Helps |
|------|-------------|
| **Junior Developers** | Safe, read-only way to explore cluster state without fear of breaking things |
| **Senior Developers** | Quick cluster health checks without context-switching to terminal |
| **On-Call Engineers** | Instant answers at 2 AM — "Which pods crashed in the last hour?" |
| **DevOps/SRE Teams** | Reduce repetitive Slack questions — self-service cluster info |
| **Team Leads/Managers** | High-level cluster health summaries without needing kubectl access |

---

## 2. Problem Statement & Why This Chatbot

### The Problems

1. **Knowledge Barrier:** Not every developer knows `kubectl` commands. They depend on DevOps engineers for basic cluster info.

2. **Context Switching:** Developers working on code must switch to terminal, remember commands, parse raw YAML/JSON output — it breaks flow.

3. **Alert Fatigue:** Multiple dashboards (Grafana, Prometheus, K8s Dashboard) create information overload. Engineers need a single, simple interface.

4. **Repetitive Questions:** "Is the payment service running?" gets asked in Slack 10 times a day. The chatbot provides self-service answers.

5. **On-Call Pain:** At 2 AM, an on-call engineer shouldn't have to remember complex kubectl commands. They should just ask: "What's broken?"

6. **Tribal Knowledge:** Runbooks and SOPs are scattered across wikis, Confluence, and team members' heads. RAG brings them into one searchable interface.

### The Solution

A chatbot that:
- **Understands natural language** → Translates to infrastructure queries
- **Connects to live K8s clusters** → Returns real-time data
- **Has your team's knowledge** → RAG-indexed runbooks and docs
- **Is safe by default** → Read-only operations, write operations require authentication
- **Is accessible from anywhere** → Embeddable widget in any internal portal

---

## 3. Architecture & Tech Stack

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer / SRE)                       │
│                    "Are all pods running in production?"             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Vite)                         │
│                                                                      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────┐  │
│  │ Floating FAB │  │ Chat Widget   │  │ Cluster Selector         │  │
│  │ Button 🤖    │  │ (Dark Theme)  │  │ (DC / DR / All)          │  │
│  └──────────────┘  └───────────────┘  └──────────────────────────┘  │
│                          Port 5173                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP POST /chat
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                         │
│                          Port 8000                                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    LangChain Agent                              │  │
│  │                                                                │  │
│  │  1. Receive user message                                       │  │
│  │  2. LLM decides intent (knowledge? cluster query? action?)     │  │
│  │  3. Select appropriate tool                                    │  │
│  │  4. Execute tool → get raw data                                │  │
│  │  5. LLM formats data into human-friendly response              │  │
│  └─────────┬──────────────┬──────────────────┬────────────────────┘  │
│            │              │                  │                       │
│            ▼              ▼                  ▼                       │
│  ┌──────────────┐ ┌──────────────┐  ┌──────────────────────────┐    │
│  │ K8s Tools    │ │ RAG Engine   │  │ Conversation Manager     │    │
│  │              │ │              │  │                          │    │
│  │ • get_pods   │ │ • ChromaDB   │  │ • Session history        │    │
│  │ • get_nodes  │ │ • Embeddings │  │ • Context window         │    │
│  │ • get_deploy │ │ • FAQ search │  │ • Per-user sessions      │    │
│  │ • get_logs   │ │              │  │                          │    │
│  │ • get_events │ │              │  │                          │    │
│  └──────┬───────┘ └──────┬───────┘  └──────────────────────────┘    │
│         │                │                                           │
└─────────┼────────────────┼───────────────────────────────────────────┘
          │                │
          ▼                ▼
┌──────────────────┐ ┌──────────────────┐
│ Kubernetes       │ │ Vector Database  │
│ Clusters         │ │ (ChromaDB)       │
│                  │ │                  │
│ ┌──────────────┐ │ │ DevOps Runbooks  │
│ │ DC Cluster   │ │ │ Troubleshooting  │
│ │ (Production) │ │ │ SOPs & Guides    │
│ └──────────────┘ │ │ K8s Best Practic │
│ ┌──────────────┐ │ └──────────────────┘
│ │ DR Cluster   │ │
│ │ (Disaster    │ │
│ │  Recovery)   │ │
│ └──────────────┘ │
└──────────────────┘
          │
          ▼
┌──────────────────┐
│ LLM Provider     │
│                  │
│ Primary: Groq    │
│ (llama-3.3-70b)  │
│                  │
│ Fallback: Ollama │
│ (local llama3)   │
└──────────────────┘
```

### Tech Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Language** | Python 3.11+ | Best AI/ML ecosystem for LLM + K8s integration |
| **API Framework** | FastAPI | High-performance async REST API |
| **LLM Framework** | LangChain (Agents + Tools) | Natural language → tool execution pipeline |
| **LLM Provider (Primary)** | Groq Cloud API | Fast inference (~3 sec), `llama-3.3-70b-versatile` |
| **LLM Provider (Fallback)** | Ollama (local) | Offline/air-gapped environments |
| **Kubernetes Client** | `kubernetes` Python SDK | Official K8s API client for cluster queries |
| **Vector Database** | ChromaDB | Local embedded vector DB for RAG |
| **Embedding Model** | `all-MiniLM-L6-v2` | Fast, lightweight sentence embeddings (~90MB) |
| **Frontend Framework** | React 19 | Component-based UI, embeddable widget |
| **Build Tool** | Vite 7 | Fast dev server and production builds |
| **Styling** | Vanilla CSS | Full control, dark theme, animations |
| **Font** | Inter (Google Fonts) | Clean, modern typography |

---

## 4. Project Folder Structure

```
devopschatbot/
│
├── Doc/
│   └── 01_PROJECT_DOCUMENTATION.md      ← THIS FILE — complete project docs
│
├── backend/
│   ├── main.py                           ← FastAPI app — API endpoints
│   ├── llm_engine.py                     ← LangChain Agent with tools + conversation memory
│   ├── rag_engine.py                     ← ChromaDB vector search for knowledge base
│   ├── ingest_faq.py                     ← Script to ingest PDFs/docs into vector DB
│   ├── k8s_tools.py                      ← [NEW] Kubernetes API functions (get_pods, etc.)
│   ├── k8s_client.py                     ← [NEW] K8s cluster connection manager
│   ├── requirements.txt                  ← Python dependencies
│   ├── .env                              ← Configuration (API keys, cluster config, ports)
│   ├── .gitignore                        ← Git ignore rules
│   └── venv/                             ← Python virtual environment
│
├── frontend/
│   └── react-chat/                       ← React frontend application
│       ├── index.html                    ← HTML entry point
│       ├── package.json                  ← NPM dependencies
│       ├── vite.config.js                ← Vite configuration
│       ├── node_modules/                 ← NPM packages
│       └── src/
│           ├── main.jsx                  ← React entry point
│           ├── App.jsx                   ← Main app — floating widget + chat popup
│           ├── ChatInput.jsx             ← Text input + send button component
│           ├── MessageBubble.jsx         ← Chat message bubble component
│           ├── TypingIndicator.jsx        ← Animated "..." typing dots
│           ├── ClusterSelector.jsx       ← [NEW] DC/DR cluster dropdown
│           ├── StatusBadge.jsx           ← [NEW] Pod/Node status indicators
│           ├── api.js                    ← API service (calls FastAPI backend)
│           └── index.css                 ← All styles (dark theme, animations)
│
├── data/
│   ├── devops_knowledge/                 ← [NEW] DevOps runbooks, SOPs, guides
│   │   ├── kubernetes_troubleshooting.md
│   │   ├── deployment_procedures.md
│   │   ├── incident_response.md
│   │   └── common_errors.md
│   ├── chroma_db/                        ← ChromaDB vector database (auto-generated)
│   └── FAQ-hudco.pdf                     ← [OLD] Will be replaced with DevOps docs
│
└── README.md                            ← Project README
```

---

## 5. Backend — Complete Details

### File: `backend/main.py`
**Purpose:** FastAPI application — the entry point for all API requests.

**What it does:**
- Creates a FastAPI app with CORS enabled (allows any frontend to call it)
- Imports `conversation_manager` from `llm_engine.py`
- Exposes REST API endpoints for chat, sessions, and cluster health
- Runs on `http://0.0.0.0:8000` with auto-reload in development

**Current Endpoints:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Health check — returns API status |
| `POST` | `/chat` | Main chat endpoint — send message, get AI response |
| `POST` | `/session/new` | Create a new chat session |
| `POST` | `/session/{id}/clear` | Clear conversation history for a session |

**Planned Endpoints (K8s Integration):**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/clusters` | List available clusters (DC, DR) |
| `GET` | `/clusters/{name}/health` | Quick health summary of a cluster |
| `POST` | `/chat` | Enhanced — supports `cluster` parameter |

**Request/Response Models:**
```python
# Chat Request
{
    "message": "Are all pods running in production?",
    "session_id": "abc-123",          # optional, auto-generated if null
    "cluster": "dc"                   # optional, "dc" | "dr" | "all"
}

# Chat Response
{
    "response": "✅ All 24 pods are running in the production namespace...",
    "session_id": "abc-123",
    "metadata": {                     # optional, included for cluster queries
        "query_type": "pod_status",
        "cluster": "dc",
        "timestamp": "2026-04-15T16:30:00Z"
    }
}
```

---

### File: `backend/llm_engine.py`
**Purpose:** The brain of the chatbot — LangChain Agent with tools, conversation memory, and RAG integration.

**Current Implementation:**
- Simple LangChain chain: `prompt | llm`
- Supports Groq (cloud) and Ollama (local) as LLM providers
- Conversation history stored in-memory per session
- RAG context injected into system prompt when relevant FAQ found

**Planned Upgrade — LangChain Agent with Tools:**
The simple chain will be upgraded to a **LangChain Agent** that can decide which tool to call:

```python
# Agent decides based on user message:
#
# "What is a pod?"           → RAG search (knowledge base)
# "Show pods in production"  → K8s Tool: get_pods(namespace="production")
# "Any nodes not ready?"     → K8s Tool: get_nodes(status="NotReady")
# "Hello, how are you?"      → General chat (no tool needed)
```

**Tools the Agent will have access to:**
| Tool Name | Description | Example Trigger |
|-----------|-------------|-----------------|
| `search_knowledge_base` | RAG search in DevOps docs | "How do I debug CrashLoopBackOff?" |
| `get_pod_status` | Get pods in a namespace | "Show all pods in production" |
| `get_pod_logs` | Get logs from a specific pod | "Show logs of auth-service" |
| `get_node_status` | Get node health | "Are all nodes ready?" |
| `get_deployments` | List deployments | "What deployments are in staging?" |
| `get_events` | Get cluster events/warnings | "Any warnings in the last hour?" |
| `get_services` | List services | "What services are exposed?" |
| `get_cluster_summary` | Overall cluster health | "Give me a cluster health report" |
| `get_resource_usage` | CPU/memory metrics | "Which pods use the most memory?" |

**Conversation Manager:**
- In-memory session storage (dict of session_id → message history)
- Auto-trims history when it exceeds `MAX_CONVERSATION_HISTORY` (default: 20 exchanges)
- Supports follow-up questions: "What about the staging namespace?" uses context from previous message

---

### File: `backend/rag_engine.py`
**Purpose:** RAG (Retrieval-Augmented Generation) engine — searches the knowledge base for relevant documentation.

**How it works:**
1. On startup, loads ChromaDB with pre-indexed DevOps documentation
2. When user asks a question, searches for top-K relevant document chunks
3. Passes the relevant context to the LLM along with the user's question
4. LLM uses the context to give accurate, documentation-backed answers

**Configuration:**
| Setting | Value | Description |
|---------|-------|-------------|
| `CHROMA_DB_DIR` | `../data/chroma_db` | ChromaDB storage location |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `COLLECTION_NAME` | `devops_knowledge` | ChromaDB collection name |
| `TOP_K` | `3` | Number of relevant chunks to retrieve |

---

### File: `backend/ingest_faq.py`
**Purpose:** Ingestion script — reads documents (PDF, Markdown) and creates vector embeddings in ChromaDB.

**Pipeline:**
```
Documents (PDF/MD) → Load → Split into chunks → Create embeddings → Store in ChromaDB
```

**Chunk Settings:**
| Setting | Value | Reason |
|---------|-------|--------|
| `CHUNK_SIZE` | 500 chars | Keeps Q&A pairs and paragraphs together |
| `CHUNK_OVERLAP` | 50 chars | Prevents cutting context at boundaries |

**Usage:**
```bash
cd backend
venv\Scripts\activate
python ingest_faq.py
```
Run once after adding/updating documents. Run again only if the source documents change.

---

### File: `backend/k8s_tools.py` [NEW — To Be Implemented]
**Purpose:** Kubernetes API functions that the LangChain Agent calls as tools.

**Planned Functions:**

```python
# --- Pod Operations ---
def get_pods(namespace: str = "default", cluster: str = "dc") -> str:
    """Get all pods in a namespace with their status."""

def get_pod_logs(pod_name: str, namespace: str = "default", 
                 tail_lines: int = 50, cluster: str = "dc") -> str:
    """Get logs from a specific pod."""

def get_crashed_pods(namespace: str = None, cluster: str = "dc") -> str:
    """Find all pods that are not in Running state."""

# --- Node Operations ---
def get_nodes(cluster: str = "dc") -> str:
    """Get all nodes with their status, capacity, and conditions."""

def get_node_health(cluster: str = "dc") -> str:
    """Quick node health summary — Ready vs NotReady count."""

# --- Deployment Operations ---
def get_deployments(namespace: str = "default", cluster: str = "dc") -> str:
    """List all deployments with replica counts and status."""

def get_deployment_detail(name: str, namespace: str = "default", 
                          cluster: str = "dc") -> str:
    """Detailed info about a specific deployment — image, replicas, strategy."""

# --- Events & Warnings ---
def get_events(namespace: str = None, event_type: str = "Warning",
               minutes: int = 60, cluster: str = "dc") -> str:
    """Get cluster events filtered by type and time window."""

# --- Services ---
def get_services(namespace: str = "default", cluster: str = "dc") -> str:
    """List all services with their types, ports, and endpoints."""

# --- Resource Usage ---
def get_resource_usage(namespace: str = "default", cluster: str = "dc") -> str:
    """Get CPU and memory usage for pods (requires metrics-server)."""

# --- Cluster Summary ---
def get_cluster_summary(cluster: str = "dc") -> str:
    """Complete cluster health report — nodes, pods, warnings, resource usage."""
```

---

### File: `backend/k8s_client.py` [NEW — To Be Implemented]
**Purpose:** Manages connections to multiple Kubernetes clusters.

**Planned Implementation:**
```python
class K8sClusterManager:
    """
    Manages connections to multiple K8s clusters (DC, DR).
    Reads cluster configs from .env or kubeconfig files.
    """
    
    def __init__(self):
        self.clusters = {}
        self._load_clusters()
    
    def get_client(self, cluster_name: str):
        """Get the K8s API client for a specific cluster."""
        
    def list_clusters(self) -> list:
        """List all configured clusters."""
        
    def health_check(self, cluster_name: str) -> dict:
        """Quick connectivity check for a cluster."""
```

**Connection Methods Supported:**
| Method | Use Case |
|--------|----------|
| **Kubeconfig file** | Local development, when you have `~/.kube/config` |
| **In-cluster config** | When chatbot runs as a pod inside the K8s cluster |
| **Service Account Token** | Remote access with a specific service account |
| **API Server URL + Token** | Direct connection to cluster API server |

---

### File: `backend/requirements.txt`
**Current Dependencies:**
```
fastapi
uvicorn[standard]
langchain
langchain-ollama
langchain-core
langchain-groq
python-dotenv
pydantic

# RAG dependencies
chromadb
pypdf
sentence-transformers
langchain-community
langchain-text-splitters
```

**Additional Dependencies Needed:**
```
# Kubernetes Integration
kubernetes                    # Official K8s Python client
urllib3                       # HTTP client (K8s SDK dependency)

# Enhanced LangChain (Agent + Tools)
langchain-experimental        # For advanced agent features

# Optional — Monitoring Integration
prometheus-api-client         # Query Prometheus metrics
requests                      # HTTP calls to Grafana/AlertManager
```

---

## 6. Frontend — Complete Details

### File: `frontend/react-chat/src/App.jsx`
**Purpose:** Main application component — the floating chat widget.

**Current Features:**
- **Floating Action Button (FAB):** 🤖 robot icon, fixed bottom-right, bounce animation
- **Chat Popup:** 350×480px dark-themed chat window with slide-up animation
- **Welcome Screen:** Shown when no messages — waving hand emoji
- **Auto-scroll:** Scrolls to latest message automatically
- **Online/Offline Status:** Checks backend API every 10 seconds
- **Session Management:** Unique session ID per browser tab
- **Error Handling:** API failures shown as error messages in chat

**States Managed:**
| State | Type | Purpose |
|-------|------|---------|
| `isOpen` | boolean | Whether chat popup is visible |
| `messages` | array | Chat messages `{role, content, timestamp}` |
| `isLoading` | boolean | Waiting for AI response |
| `isOnline` | boolean | Backend API reachability |
| `sessionId` | string | Unique session identifier |

**Planned New Features:**
- **Cluster Selector Dropdown:** Choose DC / DR / All clusters
- **Quick Action Buttons:** "Cluster Health", "Pod Status", "Recent Warnings"
- **Rich Message Cards:** Formatted tables for pod/node status
- **Copy Button:** Copy command output to clipboard
- **Dark/Light Theme Toggle:** User preference

---

### File: `frontend/react-chat/src/ChatInput.jsx`
**Purpose:** Text input area with send button.

**Features:**
- Auto-resizing textarea (grows with content, max 100px height)
- **Enter** to send, **Shift+Enter** for new line
- Disabled when backend is offline or waiting for response
- Placeholder changes to "Connecting..." when offline

---

### File: `frontend/react-chat/src/MessageBubble.jsx`
**Purpose:** Individual chat message bubble.

**Features:**
- Different styles: User messages (gradient purple, right-aligned) vs AI (dark, left-aligned)
- Avatar icons: 🧑‍💻 for user, 🤖 for AI
- Simple markdown rendering for AI messages:
  - `**bold**` → **bold**
  - `` `code` `` → inline code
  - Newlines → `<br/>`
- Timestamp display (HH:MM format)
- Slide-up animation on appearance

**Planned Enhancements:**
- Full markdown rendering (headers, lists, code blocks)
- Status badges (✅ Running, ❌ CrashLoopBackOff, ⚠️ Warning)
- Collapsible sections for long outputs
- Syntax-highlighted code blocks for logs

---

### File: `frontend/react-chat/src/TypingIndicator.jsx`
**Purpose:** Animated three-dot "..." indicator shown while waiting for AI response.

---

### File: `frontend/react-chat/src/api.js`
**Purpose:** API service module — all backend communication.

**Current Functions:**
| Function | Endpoint | Timeout | Description |
|----------|----------|---------|-------------|
| `checkApiStatus()` | `GET /` | 3 sec | Check if backend is online |
| `sendMessage(message, sessionId)` | `POST /chat` | 120 sec | Send chat message |
| `clearSession(sessionId)` | `POST /session/{id}/clear` | 5 sec | Clear session history |

**Planned New Functions:**
| Function | Endpoint | Description |
|----------|----------|-------------|
| `getClusters()` | `GET /clusters` | List available clusters |
| `getClusterHealth(name)` | `GET /clusters/{name}/health` | Quick cluster health check |

**⚠️ Important:** Backend URL is hardcoded as `http://localhost:8000`. Must be changed for production deployment.

---

### File: `frontend/react-chat/src/index.css`
**Purpose:** Complete styling for the floating chat widget.

**Design System:**
| Variable | Value | Description |
|----------|-------|-------------|
| `--bg-widget` | `#111827` | Widget background (dark navy) |
| `--bg-header` | gradient purple | Header gradient |
| `--bg-messages` | `#0f172a` | Messages area background |
| `--bg-user-msg` | gradient purple | User message bubble |
| `--bg-ai-msg` | `#1e293b` | AI message bubble |
| `--text-primary` | `#e2e8f0` | Main text color |
| `--accent` | `#667eea` | Accent/highlight color |
| `--success` | `#22c55e` | Online/success indicator |
| `--error` | `#ef4444` | Offline/error indicator |
| `--radius` | `16px` | Widget border radius |
| `--widget-width` | `350px` | Chat popup width |
| `--widget-height` | `480px` | Chat popup height |

**Responsive:** Below 440px, widget goes full-width for mobile.

---

## 7. Kubernetes Integration — Core Feature

### How It Works

The chatbot uses LangChain's **Agent + Tools** pattern to interact with Kubernetes:

```
User Message: "Are there any crashed pods in production?"
                │
                ▼
┌─────────────────────────────────────┐
│ LLM (Groq/Ollama) analyzes intent: │
│                                     │
│ Intent: "pod status check"          │
│ Namespace: "production"             │
│ Filter: "not running"               │
│                                     │
│ Decision: Call get_crashed_pods()    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ K8s Tool: get_crashed_pods()        │
│                                     │
│ → Calls K8s API                     │
│ → Filters pods where               │
│   status.phase != "Running"         │
│ → Returns raw data                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ LLM formats response:              │
│                                     │
│ "⚠️ Found 2 pods not running in    │
│  production namespace:              │
│                                     │
│  ❌ auth-service-7d4f8 →            │
│     CrashLoopBackOff (3 restarts)   │
│  ❌ payment-worker-9a2b1 →          │
│     ImagePullBackOff                │
│                                     │
│  Would you like to see the logs     │
│  for either of these pods?"         │
└─────────────────────────────────────┘
```

### Example Conversations

**Conversation 1 — Pod Health Check:**
```
User: "How are the pods in production?"
Bot:  "✅ Production namespace has 24 pods total:
       • 22 Running ✅
       • 1 CrashLoopBackOff ❌ (auth-service-7d4f8)
       • 1 Pending ⏳ (batch-processor-new-abc12)
       
       Would you like details on the problematic pods?"

User: "Yes, show me the auth-service logs"
Bot:  "📋 Last 20 lines from auth-service-7d4f8:
       
       [ERROR] 2026-04-15 10:23:45 - Database connection refused
       [ERROR] 2026-04-15 10:23:45 - Failed to connect to postgres:5432
       [INFO]  2026-04-15 10:23:46 - Retrying in 5 seconds...
       ...
       
       💡 It looks like the pod can't connect to the database.
       Check if the postgres service is running in the same namespace."
```

**Conversation 2 — Node Health:**
```
User: "Are all nodes healthy?"
Bot:  "🖥️ Cluster DC has 5 nodes:
       
       ✅ node-01  Ready    CPU: 45%  Memory: 62%
       ✅ node-02  Ready    CPU: 38%  Memory: 55%
       ✅ node-03  Ready    CPU: 72%  Memory: 78%
       ❌ node-04  NotReady CPU: --   Memory: --
       ✅ node-05  Ready    CPU: 51%  Memory: 60%
       
       ⚠️ node-04 is NotReady! Last heartbeat was 15 minutes ago.
       This could be a network issue or kubelet crash."
```

**Conversation 3 — Multi-Cluster Comparison:**
```
User: "Compare DC and DR clusters"
Bot:  "📊 Cluster Comparison:
       
       │ Metric        │ DC     │ DR     │
       │───────────────│────────│────────│
       │ Nodes          │ 5      │ 3      │
       │ Total Pods     │ 47     │ 32     │
       │ Running Pods   │ 45     │ 32     │
       │ Failed Pods    │ 2      │ 0      │
       │ Warnings       │ 3      │ 0      │
       │ CPU Avg        │ 52%    │ 35%    │
       │ Memory Avg     │ 64%    │ 48%    │
       
       ⚠️ DC has 2 failed pods and 3 warnings.
       DR looks healthy. Want details on DC issues?"
```

### Supported Queries (Natural Language → K8s API)

| What User Can Ask | What Chatbot Does |
|---|---|
| "Show all pods" / "List pods in staging" | `kubectl get pods -n staging` |
| "Any pods crashed?" / "What's broken?" | Filter pods where status ≠ Running |
| "Show logs of payment-service" | `kubectl logs <pod-name> --tail=50` |
| "How many replicas does nginx have?" | `kubectl get deployment nginx` |
| "Any warnings in the cluster?" | `kubectl get events --field-selector type=Warning` |
| "Is the API server healthy?" | Cluster health check |
| "Which pods use the most CPU?" | Metrics API → sort by CPU |
| "Describe the auth-service pod" | `kubectl describe pod <name>` |
| "What namespaces exist?" | `kubectl get namespaces` |
| "Show services in production" | `kubectl get svc -n production` |
| "Compare DC and DR" | Query both clusters, format comparison |
| "Cluster health report" | Comprehensive summary of everything |

---

## 8. RAG Pipeline — Knowledge Base

### Purpose

The RAG (Retrieval-Augmented Generation) pipeline gives the chatbot knowledge from your team's documentation. When a developer asks "How do I debug CrashLoopBackOff?", the chatbot searches your indexed runbooks and gives a contextual answer.

### What Documents to Index

| Document Type | Examples |
|--------------|---------|
| **Troubleshooting Guides** | "How to fix ImagePullBackOff", "OOMKilled debugging" |
| **Runbooks / SOPs** | Incident response procedures, escalation paths |
| **Deployment Procedures** | How to deploy, rollback, scale services |
| **Architecture Docs** | Service dependencies, network topology |
| **Common Errors** | Known issues and their fixes |
| **K8s Best Practices** | Resource limits, health checks, pod disruption budgets |
| **Team-Specific Knowledge** | Internal tools, custom operators, CI/CD pipelines |

### RAG Pipeline Flow

```
1. INGESTION (one-time, run when docs change):
   Markdown/PDF files → Split into chunks → Create embeddings → Store in ChromaDB

2. RETRIEVAL (every chat message):
   User question → Create embedding → Search ChromaDB → Get top-3 relevant chunks

3. GENERATION:
   System prompt + relevant chunks + user question → LLM → Human-friendly answer
```

### Storage

- **Source Documents:** `data/devops_knowledge/` (Markdown and PDF files)
- **Vector Database:** `data/chroma_db/` (auto-generated by ingestion script)
- **Embedding Model:** `all-MiniLM-L6-v2` (~90MB, runs locally, no API needed)

---

## 9. Feature Roadmap & Phases

### Phase 1 — Foundation ✅ (COMPLETED)

| Task | Status | Notes |
|------|--------|-------|
| Project structure setup | ✅ Done | `backend/`, `frontend/`, `data/`, `Doc/` |
| Python backend with FastAPI | ✅ Done | `main.py` — REST API |
| LLM integration (Groq + Ollama) | ✅ Done | `llm_engine.py` — dual provider support |
| Conversation memory | ✅ Done | In-memory per-session history |
| React floating chat widget | ✅ Done | FAB + popup + dark theme |
| RAG pipeline with ChromaDB | ✅ Done | `rag_engine.py` + `ingest_faq.py` |
| PDF ingestion | ✅ Done | HUDCO FAQ indexed (will replace with DevOps docs) |

---

### Phase 2 — DevOps Transformation 🔲 (NEXT)

| Task | Priority | Description |
|------|----------|-------------|
| Replace FAQ data with DevOps runbooks | High | Create/add Kubernetes troubleshooting guides |
| Update system prompt for DevOps | High | Change personality from HUDCO assistant to DevOps assistant |
| Re-ingest knowledge base | High | Run ingestion script with new DevOps documents |
| Update frontend branding | Medium | Change title, icons, colors to DevOps theme |
| Add quick action buttons | Medium | "Cluster Health", "Pod Status" buttons in welcome screen |
| Improve markdown rendering | Medium | Better formatting for code blocks, tables, logs |

---

### Phase 3 — Kubernetes Cluster Integration 🔲

| Task | Priority | Description |
|------|----------|-------------|
| Install `kubernetes` Python SDK | High | `pip install kubernetes` |
| Create `k8s_client.py` | High | Cluster connection manager (DC + DR) |
| Create `k8s_tools.py` | High | All K8s API functions as LangChain tools |
| Upgrade LLM engine to Agent | High | Replace simple chain with LangChain Agent + Tools |
| Implement `get_pods` tool | High | Core feature — pod status queries |
| Implement `get_nodes` tool | High | Node health checks |
| Implement `get_deployments` tool | High | Deployment info |
| Implement `get_pod_logs` tool | High | Log retrieval |
| Implement `get_events` tool | Medium | Cluster warnings/events |
| Implement `get_services` tool | Medium | Service listing |
| Implement `get_cluster_summary` tool | Medium | All-in-one health report |
| Implement `get_resource_usage` tool | Low | CPU/memory metrics (needs metrics-server) |
| Add cluster selector to frontend | Medium | DC / DR / All dropdown |
| Add `/clusters` API endpoint | Medium | List and health-check clusters |
| Test with real cluster | High | End-to-end testing |

---

### Phase 4 — Multi-Cluster & Monitoring Integration 🔲

| Task | Priority | Description |
|------|----------|-------------|
| Multi-cluster comparison | High | "Compare DC vs DR" queries |
| Prometheus integration | Medium | Pull metrics from Prometheus |
| Grafana dashboard links | Low | Include relevant Grafana links in responses |
| AlertManager integration | Medium | Show active alerts |
| Historical data | Low | "Show pod restarts in last 24 hours" |

---

### Phase 5 — Write Operations & Actions 🔲 (Requires Careful Security)

| Task | Priority | Description |
|------|----------|-------------|
| Restart pod | Medium | With confirmation prompt |
| Scale deployment | Medium | "Scale nginx to 5 replicas" |
| Rollback deployment | Medium | "Rollback to previous version" |
| RBAC integration | High | Only authorized users can perform write actions |
| Audit logging | High | Log all write operations with user, time, action |
| Approval workflow | Medium | Write actions require approval from a second user |

---

### Phase 6 — Production & Integration 🔲

| Task | Priority | Description |
|------|----------|-------------|
| Deploy backend as service | High | Docker container or Windows Service |
| Package React as embeddable widget | High | Single JS bundle for embedding in portals |
| SSL/HTTPS setup | High | Secure all API communications |
| Authentication integration | High | SSO / LDAP / token-based auth |
| Embed in internal portal | Medium | Drop-in `<script>` tag |
| Production testing | High | Load testing, error scenarios |

---

### Phase 7 — Advanced Features 🔲 (Future)

| Task | Description |
|------|-------------|
| Feedback buttons (👍/👎) | Rate AI responses to improve quality |
| Chat history persistence | Save to database instead of in-memory |
| Admin panel | Manage knowledge base, view analytics |
| Multi-language support | Hindi, regional language support |
| Slack/Teams integration | Chatbot available in team messaging apps |
| Scheduled reports | "Send me cluster health every morning at 9 AM" |
| Anomaly detection | Proactive alerts — "Pod X has been restarting every 5 minutes" |
| Cost analysis | "How much is this namespace costing us?" |
| CI/CD pipeline status | "What's the status of the latest deployment pipeline?" |

---

## 10. API Endpoints Reference

**Base URL:** `http://localhost:8000`

### GET `/` — Health Check
```json
// Response
{
    "status": "online",
    "service": "DevOps Chatbot API",
    "model": "llama-3.3-70b-versatile",
    "clusters_connected": 2
}
```

### POST `/chat` — Send Message
```json
// Request
{
    "message": "Show crashed pods in production",
    "session_id": "abc-123",
    "cluster": "dc"
}

// Response
{
    "response": "⚠️ Found 2 crashed pods in production namespace...",
    "session_id": "abc-123"
}
```

### POST `/session/new` — Create New Session
```json
// Response
{
    "session_id": "uuid-here",
    "message": "New session created"
}
```

### POST `/session/{session_id}/clear` — Clear History
```json
// Response
{
    "session_id": "uuid-here",
    "message": "Session history cleared"
}
```

### GET `/clusters` — List Clusters [PLANNED]
```json
// Response
{
    "clusters": [
        {
            "name": "dc",
            "display_name": "Data Center (Production)",
            "status": "connected",
            "api_server": "https://10.0.1.100:6443"
        },
        {
            "name": "dr",
            "display_name": "Disaster Recovery",
            "status": "connected",
            "api_server": "https://10.0.2.100:6443"
        }
    ]
}
```

### GET `/clusters/{name}/health` — Cluster Health [PLANNED]
```json
// Response
{
    "cluster": "dc",
    "status": "healthy",
    "nodes": { "total": 5, "ready": 4, "not_ready": 1 },
    "pods": { "total": 47, "running": 45, "failed": 2 },
    "warnings": 3,
    "timestamp": "2026-04-15T16:30:00Z"
}
```

### Swagger Documentation
Auto-generated API docs available at: `http://localhost:8000/docs`

---

## 11. How to Run the Project

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build tool |
| Groq API Key | — | LLM inference (free tier) |
| kubectl (optional) | latest | For K8s features — or use kubeconfig file |
| Ollama (optional) | latest | Local LLM fallback |

### Step 1: Start the Backend

```bash
cd d:\New folder\devopschatbot\backend

# Activate virtual environment
venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
✅ Using Groq API with model: llama-3.3-70b-versatile
🧠 RAG mode: ON — FAQ data will be used to answer questions
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start the React Frontend

```bash
cd d:\New folder\devopschatbot\frontend\react-chat

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Expected output:**
```
VITE v7.3.1  ready in 300 ms
➜  Local:   http://localhost:5173/
```

### Step 3: Open in Browser

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | Chat UI (React floating widget) |
| http://localhost:8000/docs | API documentation (Swagger) |
| http://localhost:8000/ | API health check |

### Step 4: Test

1. Click the bouncing 🤖 robot icon (bottom-right corner)
2. Chat popup opens with welcome message
3. Type: "Hello" → AI responds in ~2-3 seconds
4. Test DevOps queries once K8s integration is done

### Step 5: Re-index Knowledge Base (when documents change)

```bash
cd d:\New folder\devopschatbot\backend
venv\Scripts\activate
python ingest_faq.py
```

---

## 12. Configuration Reference

### Backend `.env` — All Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | `"groq"` for cloud, `"ollama"` for local |
| `GROQ_API_KEY` | *(required)* | API key from console.groq.com |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model (70B = better reasoning for tool use) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8000` | FastAPI port |
| `CHATBOT_NAME` | `DevOps Assistant` | Bot name in system prompt |
| `MAX_CONVERSATION_HISTORY` | `20` | Max exchanges to keep per session |

**Planned K8s Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `K8S_DC_KUBECONFIG` | `~/.kube/config` | Path to DC cluster kubeconfig |
| `K8S_DR_KUBECONFIG` | *(none)* | Path to DR cluster kubeconfig |
| `K8S_DC_API_SERVER` | *(none)* | DC cluster API server URL |
| `K8S_DR_API_SERVER` | *(none)* | DR cluster API server URL |
| `K8S_DC_TOKEN` | *(none)* | Service account token for DC |
| `K8S_DR_TOKEN` | *(none)* | Service account token for DR |
| `K8S_DEFAULT_NAMESPACE` | `default` | Default namespace for queries |
| `K8S_READ_ONLY` | `true` | Restrict to read-only operations |

### Frontend Configuration

**In `api.js`:**
| Variable | Value | Description |
|----------|-------|-------------|
| `API_URL` | `http://localhost:8000` | Backend API URL — **change for production** |

---

## 13. Security & Access Control

### Read-Only Mode (Default)

By default, the chatbot operates in **read-only mode** — it can only query information, never modify the cluster.

```
K8S_READ_ONLY=true   ← Default: only GET operations allowed
```

### Security Measures (Planned)

| Measure | Description |
|---------|-------------|
| **Read-only by default** | No create/update/delete operations unless explicitly enabled |
| **Service Account** | Use a K8s service account with minimal RBAC permissions |
| **RBAC for write ops** | Write operations (restart, scale) require authenticated user with admin role |
| **Audit logging** | All queries and actions logged with user ID, timestamp, cluster, action |
| **Rate limiting** | Prevent abuse — max 30 requests/minute per user |
| **Input sanitization** | Prevent prompt injection and malicious queries |
| **No secrets exposure** | Never return secrets, configmaps with sensitive data, or environment variables |
| **Namespace restrictions** | Configurable list of namespaces the chatbot can access |

### Recommended K8s RBAC for Chatbot Service Account

```yaml
# ClusterRole — Read-only access for the chatbot
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: devops-chatbot-readonly
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "nodes", "events", "namespaces"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["metrics.k8s.io"]
    resources: ["pods", "nodes"]
    verbs: ["get", "list"]
```

---

## 14. Deployment Guide

### Option A: Run Locally (Development)

Good for development and testing.
```bash
# Terminal 1 — Backend
cd backend && venv\Scripts\activate && python -m uvicorn main:app --port 8000 --reload

# Terminal 2 — Frontend
cd frontend\react-chat && npm run dev
```

### Option B: Docker Deployment (Production)

**Docker Compose (planned):**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./data:/app/data
      - ~/.kube/config:/app/.kube/config:ro  # K8s config
    restart: unless-stopped

  frontend:
    build: ./frontend/react-chat
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Option C: Deploy as K8s Pod (In-Cluster)

When the chatbot runs as a pod inside the Kubernetes cluster:
- Uses `in_cluster_config()` — no kubeconfig needed
- Assign a service account with the appropriate RBAC
- Can access the cluster API directly

```yaml
# Deployment for the chatbot itself (planned)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-chatbot
  namespace: tools
spec:
  replicas: 1
  template:
    spec:
      serviceAccountName: devops-chatbot-sa
      containers:
        - name: backend
          image: devops-chatbot-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: chatbot-env
```

---

## 15. Troubleshooting & Known Issues

### Backend Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `model_decommissioned` error | Groq model name is outdated | Update `GROQ_MODEL` in `.env` with a valid model |
| Ollama very slow (20+ sec) | Running on CPU without GPU | Switch to Groq: `LLM_PROVIDER=groq` in `.env` |
| `langchain-groq` not found | Not in requirements.txt | `pip install langchain-groq` |
| RAG mode OFF | ChromaDB not created yet | Run `python ingest_faq.py` first |
| K8s connection refused | Wrong kubeconfig or cluster not reachable | Check `K8S_DC_KUBECONFIG` path and cluster connectivity |

### Frontend Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Offline" status | Backend not running | Start backend first |
| CORS errors | Backend CORS not configured | Currently allows all origins (`*`). Restrict in production |
| Chat history lost on restart | In-memory storage (by design) | Will add DB persistence in Phase 7 |

### Kubernetes Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Forbidden" errors | Service account lacks RBAC permissions | Apply the ClusterRole and RoleBinding |
| Metrics not available | metrics-server not installed | Install metrics-server in the cluster |
| Slow K8s queries | Large clusters with many pods | Add namespace filtering, pagination |
| Token expired | Service account token rotation | Use auto-renewing token or kubeconfig |

### Groq Free Tier Limits

| Limit | Value |
|-------|-------|
| Requests per minute | 30 |
| Requests per day | 14,400 |
| Console | https://console.groq.com |

---

## 16. Decisions Made & Why

### Decision 1: Python over JavaScript for Backend
- **Why:** Python's AI/ML ecosystem is far superior. LangChain Python has 50K+ GitHub stars. The `kubernetes` Python SDK is mature and well-documented.
- **Trade-off:** Frontend is React (JavaScript), but they communicate via REST API — backend language doesn't matter to the frontend.

### Decision 2: Groq over Local Ollama
- **Why:** Ollama on CPU: ~20–60 sec per response. Groq: ~2–3 sec. The 70B model on Groq also reasons better for tool selection.
- **Fallback:** Ollama is still supported for air-gapped/offline environments.

### Decision 3: LangChain Agent over Simple Chain
- **Why:** A simple chain can only do prompt → response. An Agent can decide which tool to call, making it possible to route queries to K8s API, RAG, or general chat as needed.

### Decision 4: ChromaDB over Qdrant/Pinecone
- **Why:** ChromaDB is embedded (zero setup, no separate server). Perfect for development and small-to-medium knowledge bases. Can be upgraded to Qdrant later if needed.

### Decision 5: Floating Widget over Full-Page Chat
- **Why:** The widget can be embedded into any internal portal with a `<script>` tag. Doesn't take over the page. Same pattern used by Intercom, Crisp, and Tawk.to.

### Decision 6: Read-Only by Default
- **Why:** Safety first. A chatbot that can restart pods or scale deployments is dangerous without proper authentication. Start read-only, add write operations only with RBAC and audit logging.

### Decision 7: 70B Model over 8B Model
- **Why:** The 70B model (`llama-3.3-70b-versatile`) is significantly better at understanding intent, selecting the right tool, and formatting structured data. The 8B model was used initially for speed but lacked reasoning quality for agent-based workflows.

---

## 17. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Slack Bot Integration** | Chat with the bot directly in Slack channels | Medium |
| **Microsoft Teams Integration** | Embed in Teams for enterprise environments | Medium |
| **Scheduled Reports** | "Send cluster health every morning at 9 AM" | Low |
| **Anomaly Detection** | Proactive alerts: "Pod X restarted 5 times in 1 hour" | Medium |
| **Cost Analysis** | "How much is the staging namespace costing?" | Low |
| **CI/CD Pipeline Status** | "What's the status of the latest Jenkins/GitLab pipeline?" | Medium |
| **Helm Chart Info** | "What Helm charts are installed? What version?" | Low |
| **Network Policy Viewer** | "Can pod A talk to pod B?" | Low |
| **Config Drift Detection** | "Are all replicas running the same image version?" | Medium |
| **Incident Timeline** | "Show me everything that happened in the last 2 hours" | Medium |
| **Voice Input** | Speech-to-text for hands-free queries | Low |
| **Mobile App** | React Native app for on-the-go monitoring | Low |
| **Plugin System** | Let teams add custom tools and data sources | Low |

---

## Quick Reference — Commands Cheat Sheet

```bash
# ─── START BACKEND ──────────────────────────────────
cd d:\New folder\devopschatbot\backend
venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# ─── START FRONTEND ─────────────────────────────────
cd d:\New folder\devopschatbot\frontend\react-chat
npm run dev

# ─── RE-INDEX KNOWLEDGE BASE ───────────────────────
cd d:\New folder\devopschatbot\backend
python ingest_faq.py

# ─── TEST API ───────────────────────────────────────
curl http://localhost:8000/
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Hello\"}"

# ─── INSTALL NEW PYTHON PACKAGE ────────────────────
cd d:\New folder\devopschatbot\backend
venv\Scripts\pip install PACKAGE_NAME

# ─── BUILD FRONTEND FOR PRODUCTION ─────────────────
cd d:\New folder\devopschatbot\frontend\react-chat
npm run build

# ─── SWITCH LLM PROVIDER ──────────────────────────
# Edit backend/.env:
#   LLM_PROVIDER=groq    → Cloud (fast, 3 sec)
#   LLM_PROVIDER=ollama  → Local (offline, 20+ sec)
# Then restart the backend
```

---

*This document should be updated as each phase progresses. Last updated: 15 April 2026.*
