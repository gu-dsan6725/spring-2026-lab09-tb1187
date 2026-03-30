import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from agent import Agent  # Import Agent class from agent.py

app = FastAPI(
    title="Memory Agent API",
    description="Multi-tenant conversational agent with semantic memory",
    version="1.0.0"
)

# Resolve API key from environment at startup
api_key: Optional[str] = (
    os.getenv("ANTHROPIC_API_KEY") or
    os.getenv("GROQ_API_KEY") or
    os.getenv("OPENAI_API_KEY") or
    os.getenv("GEMINI_API_KEY")
)

# Session cache: run_id -> Agent instance
# ONE Agent per session (run_id) maintained in memory
_session_cache: Dict[str, Agent] = {}


def _get_or_create_agent(user_id: str, run_id: str) -> Agent:
    """Get existing Agent for session or create new one."""
    if run_id in _session_cache:
        return _session_cache[run_id]

    # Create new agent for this session
    agent = Agent(user_id=user_id, run_id=run_id, api_key=api_key)
    _session_cache[run_id] = agent
    return agent


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class InvocationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for memory isolation")
    run_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    query: str = Field(..., description="User's message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context/tags")


class InvocationResponse(BaseModel):
    user_id: str
    run_id: str
    response: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/ping")
def ping():
    """Health check endpoint."""
    return {"status": "ok", "message": "Memory Agent API is running"}


@app.post("/invocation", response_model=InvocationResponse)
def invocation(request: InvocationRequest):
    """Main conversation endpoint."""
    # Auto-generate run_id if not provided
    run_id = request.run_id or str(uuid.uuid4())[:8]

    try:
        agent = _get_or_create_agent(user_id=request.user_id, run_id=run_id)
        response_text = agent.chat(request.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return InvocationResponse(
        user_id=request.user_id,
        run_id=run_id,
        response=response_text,
    )