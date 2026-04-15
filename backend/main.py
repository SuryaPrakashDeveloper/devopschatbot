
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

from llm_engine import conversation_manager

# --- App Setup ---
app = FastAPI(
    title="DevOps Chatbot API",
    description="DevOps AI Assistant — Kubernetes, Docker, CI/CD & Infrastructure",
    version="2.0.0",
)

# CORS — allow Streamlit and any frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class SessionResponse(BaseModel):
    session_id: str
    message: str


# --- Endpoints ---

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "DevOps Chatbot API",
        "provider": os.getenv("LLM_PROVIDER", "groq"),
        "model": os.getenv("GROQ_MODEL", os.getenv("OLLAMA_MODEL", "llama3")),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Create or use existing session
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response = await conversation_manager.chat(session_id, request.message)
        return ChatResponse(
            response=response,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@app.post("/session/new", response_model=SessionResponse)
async def new_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    return SessionResponse(
        session_id=session_id,
        message="New session created",
    )


@app.post("/session/{session_id}/clear", response_model=SessionResponse)
async def clear_session(session_id: str):
    """Clear the conversation history for a session."""
    conversation_manager.clear_session(session_id)
    return SessionResponse(
        session_id=session_id,
        message="Session history cleared",
    )


# --- Run ---
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
