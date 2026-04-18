"""
LLM Engine — DevOps Chatbot (Optimized v2)
=============================================
Supports both Groq (fast cloud) and Ollama (local) with conversation memory.
RAG support — answers from DevOps knowledge base (Kubernetes, Docker, logs).

v2 Changes:
- Strict system prompt (concise, structured, no filler)
- Dynamic format templates based on query intent
- Response formatter integration (post-processing)
- Smart RAG context injection
- Reduced temperature (0.7 → 0.3) for focused answers
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# RAG Engine — searches DevOps knowledge base
from rag_engine import faq_retriever

# Response Formatter — post-processes LLM output
from response_formatter import classify_query, get_format_template, format_response, format_stream_response

load_dotenv()

# --- Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq" or "ollama"
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "DevOps Assistant")
MAX_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))

# System prompt — DevOps focused, STRICT formatting rules
SYSTEM_PROMPT = f"""You are {CHATBOT_NAME}, a production-grade DevOps AI assistant.

YOUR EXPERTISE: Kubernetes, Docker, CI/CD, Monitoring, Linux, Cloud Infrastructure, Application Logs.

STRICT RESPONSE RULES:
1. Keep answers under 150 words unless user explicitly asks for detail.
2. Use bullet points and numbered steps — NEVER paragraphs.
3. Prioritize the most common real-world issues first (80/20 rule).
4. Give step-by-step debug flows with actual commands in code blocks.
5. NO filler phrases — no "Great question!", no "Sure, I'd be happy to help".
6. NO "follow-up topics" or "related reading" sections unless user asks.
7. Use ONLY these emojis for status: 🔴 critical, 🟡 warning, 🟢 healthy, ⚡ action, 🧠 tip, ❌ error, ✅ success.
8. Code blocks MUST specify the language (```bash, ```yaml, ```json).
9. Maximum 5 bullet points per section.
10. Be confident and direct — never say "I think" or "I believe".
11. For "not found" queries — suggest closest match, don't apologize.
12. Start answers with the most important information first.

CASUAL/NON-TECHNICAL INPUT HANDLING (CRITICAL RULES):
- MATCH USER ENERGY: If user sends 1-3 words, reply in 1 SHORT sentence only. Never write paragraphs for greetings.
- First greeting → 1 short sentence. Example length: "👋 Hi! How can I help?"
- NEVER re-introduce yourself or list your capabilities after the first greeting. User already knows.
- NEVER repeat the exact same response twice. Always vary your wording.
- NEVER say "Error" or "Irrelevant Input" for casual messages. Be human and natural.
- For random/nonsense → Light humor + redirect, 1 sentence max.
- For off-topic → Politely redirect to DevOps, 1 sentence max.
- Keep ALL casual responses to maximum 1 SHORT sentence (under 15 words).

{{casual_context}}

RESPONSE STYLE:
- Think like Datadog / AWS CLI help — short, structured, actionable.
- Every command you show should be copy-paste ready.
- If showing multiple commands, number them in order of execution.

{{format_template}}

{{faq_context}}
"""

# --- Initialize LLM based on provider ---
if LLM_PROVIDER == "groq":
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.3,  # Lower = more focused, less rambling
    )
    print(f"✅ Using Groq API with model: {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
else:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        temperature=0.3,  # Lower = more focused, less rambling
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

print(f"✨ Response optimizer: ON — Query intent classification + format templates + post-processing")


class ConversationManager:
    """Manages conversation sessions with history and conversation state."""

    def __init__(self):
        self.sessions: dict[str, list] = {}
        self.casual_counts: dict[str, int] = {}  # Track consecutive casual messages per session

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
        self.casual_counts[session_id] = 0

    # --- Hardcoded casual responses (no LLM needed) ---
    CASUAL_RESPONSES = {
        1: "👋 Hi! DevOps Buddy is here, How can I help?",
        2: "😄 Hey again! What would you like help with?",
        3: "👀 Getting a lot of hellos 😄\nAsk me anything about Kubernetes or debugging or related Logs.",
        4: "🤔 Looks like you're repeating inputs.\n\nIf you need help, you can contact DevOps support:\n📞 9876543210",
    }
    CASUAL_COOLDOWN = "⏳ Too many repeated inputs.\n\nPlease wait a few seconds before sending another message."

    def _get_casual_response(self, session_id: str) -> str:
        """Get hardcoded casual response based on count. No LLM call needed."""
        self.casual_counts[session_id] = self.casual_counts.get(session_id, 0) + 1
        count = self.casual_counts[session_id]

        if count >= 5:
            return self.CASUAL_COOLDOWN
        return self.CASUAL_RESPONSES.get(count, self.CASUAL_COOLDOWN)

    def _build_context(self, session_id: str, user_message: str) -> tuple[str, str]:
        """
        Build RAG context and format template for the query.
        Returns: (faq_context, format_template)
        """
        # --- Classify query intent ---
        intent = classify_query(user_message)
        format_template = f"--- RESPONSE FORMAT FOR THIS QUERY ---\n{get_format_template(intent)}\n--- END FORMAT ---"

        # Reset casual counter when user sends a real question
        if intent != "casual":
            self.casual_counts[session_id] = 0

        # --- RAG: Search DevOps knowledge base (skip for casual) ---
        faq_context = ""
        if intent != "casual" and faq_retriever.is_ready():
            context = faq_retriever.search(user_message)
            if context:
                faq_context = (
                    f"📚 KNOWLEDGE BASE CONTEXT (use this data to answer):\n\n"
                    f"{context}\n\n"
                    f"INSTRUCTION: Base your answer on this context. "
                    f"If context doesn't fully cover the question, supplement with your knowledge but keep it brief."
                )

        return faq_context, format_template

    async def chat(self, session_id: str, user_message: str) -> str:
        history = self.get_history(session_id)
        intent = classify_query(user_message)

        # --- Casual: return hardcoded response, skip LLM ---
        if intent == "casual":
            ai_response = self._get_casual_response(session_id)
            self.add_message(session_id, "human", user_message)
            self.add_message(session_id, "ai", ai_response)
            return ai_response

        # --- Technical: use LLM ---
        faq_context, format_template = self._build_context(session_id, user_message)

        response = await chain.ainvoke({
            "history": history,
            "input": user_message,
            "faq_context": faq_context,
            "format_template": format_template,
            "casual_context": "",  # Empty for technical queries
        })

        # Post-process the response
        ai_response = format_response(response.content, intent=intent)

        self.add_message(session_id, "human", user_message)
        self.add_message(session_id, "ai", ai_response)

        return ai_response

    async def chat_stream(self, session_id: str, user_message: str):
        """Stream the AI response token-by-token (async generator).
        
        For casual messages: yields hardcoded response directly (no LLM call).
        For technical messages: collects full LLM response, applies formatter, then yields.
        """
        intent = classify_query(user_message)

        # --- Casual: yield hardcoded response, skip LLM ---
        if intent == "casual":
            ai_response = self._get_casual_response(session_id)
            self.add_message(session_id, "human", user_message)
            self.add_message(session_id, "ai", ai_response)

            # Yield word-by-word for streaming effect
            words = ai_response.split(' ')
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield word + ' '
                else:
                    yield word
            return

        # --- Technical: use LLM ---
        history = self.get_history(session_id)
        faq_context, format_template = self._build_context(session_id, user_message)

        # Collect full response first for formatting
        full_response = ""

        async for chunk in chain.astream({
            "history": history,
            "input": user_message,
            "faq_context": faq_context,
            "format_template": format_template,
            "casual_context": "",  # Empty for technical queries
        }):
            token = chunk.content
            if token:
                full_response += token

        # Apply formatter to the complete response
        formatted_response = format_stream_response(full_response, intent=intent)

        # Yield the formatted response word-by-word for smooth display
        words = formatted_response.split(' ')
        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield word + ' '
            else:
                yield word

        # Save to history after streaming completes
        self.add_message(session_id, "human", user_message)
        self.add_message(session_id, "ai", formatted_response)


# Global instance
conversation_manager = ConversationManager()

