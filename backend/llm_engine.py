"""
LLM Engine — DevOps Chatbot
============================
Supports both Groq (fast cloud) and Ollama (local) with conversation memory.
RAG support — answers from DevOps knowledge base (Kubernetes, Docker, logs).
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# RAG Engine — searches DevOps knowledge base
from rag_engine import faq_retriever

load_dotenv()

# --- Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq" or "ollama"
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "DevOps Assistant")
MAX_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))

# System prompt — DevOps focused with RAG context placeholder
SYSTEM_PROMPT = f"""You are {CHATBOT_NAME}, an expert AI assistant specialized in DevOps, Kubernetes, Docker, and cloud infrastructure.

YOUR EXPERTISE:
- Kubernetes: Pods, Deployments, Services, Nodes, Namespaces, ConfigMaps, Secrets, RBAC, Helm, operators
- Docker: Containers, Images, Dockerfiles, Docker Compose, networking, volumes
- CI/CD: Jenkins, GitLab CI, GitHub Actions, ArgoCD
- Monitoring: Prometheus, Grafana, AlertManager, ELK Stack
- Networking: Ingress, Load Balancers, DNS, Service Mesh (Istio/Linkerd)
- Cloud: AWS, Azure, GCP basics
- Linux: Shell scripting, system administration, troubleshooting
- Application logs: Reading and analyzing Spring Boot, Nginx, Node.js, and Java application logs

YOUR PERSONALITY:
- Be professional, precise, and technically detailed.
- Use emojis to make responses engaging (e.g. ✅ ❌ ⚠️ 🔧 📊 🐳 ☸️).
- Structure answers with bullet points, code blocks, and formatted tables when helpful.
- When showing commands, use proper code formatting with backticks.
- After answering, suggest related follow-up topics or commands.
- If you detect an error pattern in logs, explain the root cause and suggest fixes.

IMPORTANT RULES:
1. If DevOps knowledge base context is provided below, ALWAYS prioritize that data to answer the question.
2. If the context answers the user's question, use it directly. Rephrase it in a detailed DevOps-friendly way.
3. If the context does NOT have the answer, use your general DevOps knowledge to help. Mention it's from general knowledge.
4. If no context is provided, respond as a general DevOps expert.
5. Give detailed, actionable answers with real commands and examples. Never give vague one-liner answers.
6. When analyzing logs, identify error patterns, timestamps, HTTP status codes, and potential issues.
7. For Kubernetes questions, always include relevant kubectl commands the user can run.
8. For Docker questions, include relevant docker/docker-compose commands.

LOG ANALYSIS GUIDELINES:
- Look for ERROR, WARN, Exception, stack traces, HTTP 4xx/5xx status codes
- Note timestamps to identify when issues started
- Identify service names and which microservice is affected
- Suggest debugging steps and kubectl/docker commands to investigate further

{{faq_context}}
"""

# --- Initialize LLM based on provider ---
if LLM_PROVIDER == "groq":
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.7,
    )
    print(f"✅ Using Groq API with model: {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
else:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        temperature=0.7,
    )
    print(f"✅ Using Ollama (local) with model: {os.getenv('OLLAMA_MODEL', 'llama3')}")

# --- Prompt template with conversation history ---
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# Build the chain
chain = prompt | llm

if faq_retriever.is_ready():
    print(f"🧠 RAG mode: ON — DevOps knowledge base will be used to answer questions")
else:
    print(f"⚠️  RAG mode: OFF — Run 'python ingest_data.py' to enable knowledge base answers")


class ConversationManager:
    """Manages conversation sessions with history."""

    def __init__(self):
        self.sessions: dict[str, list] = {}

    def get_history(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_history(session_id)
        if role == "human":
            history.append(HumanMessage(content=content))
        else:
            history.append(AIMessage(content=content))

        if len(history) > MAX_HISTORY * 2:
            self.sessions[session_id] = history[-(MAX_HISTORY * 2):]

    def clear_session(self, session_id: str):
        self.sessions[session_id] = []

    async def chat(self, session_id: str, user_message: str) -> str:
        history = self.get_history(session_id)

        # --- RAG: Search DevOps knowledge base for relevant context ---
        faq_context = ""
        if faq_retriever.is_ready():
            context = faq_retriever.search(user_message)
            if context:
                faq_context = f"--- RELEVANT DEVOPS KNOWLEDGE ---\n{context}\n--- END KNOWLEDGE ---"

        response = await chain.ainvoke({
            "history": history,
            "input": user_message,
            "faq_context": faq_context,
        })

        ai_response = response.content

        self.add_message(session_id, "human", user_message)
        self.add_message(session_id, "ai", ai_response)

        return ai_response

    async def chat_stream(self, session_id: str, user_message: str):
        """Stream the AI response token-by-token (async generator)."""
        history = self.get_history(session_id)

        # --- RAG: Search DevOps knowledge base for relevant context ---
        faq_context = ""
        if faq_retriever.is_ready():
            context = faq_retriever.search(user_message)
            if context:
                faq_context = f"--- RELEVANT DEVOPS KNOWLEDGE ---\n{context}\n--- END KNOWLEDGE ---"

        # Collect full response for saving to history
        full_response = ""

        async for chunk in chain.astream({
            "history": history,
            "input": user_message,
            "faq_context": faq_context,
        }):
            token = chunk.content
            if token:
                full_response += token
                yield token

        # Save to history after streaming completes
        self.add_message(session_id, "human", user_message)
        self.add_message(session_id, "ai", full_response)


# Global instance
conversation_manager = ConversationManager()
