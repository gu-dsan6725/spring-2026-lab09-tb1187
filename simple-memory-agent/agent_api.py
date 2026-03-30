import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from agent import Agent  # Import Agent class from agent.py
from mem0 import MemoryClient

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


# ---------------------------------------------------------------------------
# Debug endpoints (remove before production)
# ---------------------------------------------------------------------------

def _mem0_client() -> MemoryClient:
    mem0_key = os.getenv("MEM0_API_KEY")
    if not mem0_key:
        raise HTTPException(status_code=500, detail="MEM0_API_KEY not set")
    return MemoryClient(api_key=mem0_key)


@app.get("/debug/users")
def debug_users():
    """Show raw memory.users() response from Mem0."""
    client = _mem0_client()
    return {"raw_users": client.users()}


@app.get("/debug/memories/{user_id}")
def debug_memories(user_id: str):
    """Show all memories for a user via get_all() with user_id filter."""
    client = _mem0_client()
    by_user = client.get_all(filters={"user_id": user_id})
    return {"user_id": user_id, "results": by_user}


@app.get("/debug/search/{user_id}")
def debug_search(user_id: str, q: str = "anything"):
    """Search memories with user_id filter and show raw Mem0 response."""
    client = _mem0_client()
    results = client.search(query=q, filters={"user_id": user_id}, limit=10)
    return {"user_id": user_id, "query": q, "raw_results": results}


@app.get("/debug/search-by-run/{run_id}")
def debug_search_by_run(run_id: str, q: str = "anything"):
    """Search memories filtered by a single run_id."""
    client = _mem0_client()
    results = client.search(query=q, filters={"run_id": run_id}, limit=10)
    return {"run_id": run_id, "query": q, "raw_results": results}


@app.get("/debug/getall-by-run/{run_id}")
def debug_getall_by_run(run_id: str):
    """Get all memories for a specific run_id."""
    client = _mem0_client()
    results = client.get_all(filters={"run_id": run_id})
    return {"run_id": run_id, "results": results}


@app.get("/debug/search-or/{user_id}")
def debug_search_or(user_id: str, q: str = "anything"):
    """Search with OR filter across all runs for a user."""
    client = _mem0_client()
    # Build OR filter from actual runs
    users_data = client.users()
    if isinstance(users_data, dict):
        results_list = users_data.get('results', [])
    else:
        results_list = getattr(users_data, 'results', [])

    user_runs = []
    for u in results_list:
        u_type = u.get('type') if isinstance(u, dict) else getattr(u, 'type', None)
        u_name = u.get('name', '') if isinstance(u, dict) else getattr(u, 'name', '')
        if u_type == 'run' and u_name.startswith(user_id + '-'):
            user_runs.append(u_name)

    filters = {'OR': [{'run_id': r} for r in user_runs]}
    results = client.search(query=q, filters=filters, limit=10)
    return {"user_id": user_id, "runs_found": user_runs, "filters": filters, "raw_results": results}


@app.get("/debug/filter-formats/{user_id}")
def debug_filter_formats(user_id: str, q: str = "software engineer", run_id: str = "alice-session-1"):
    """Test different Mem0 v2 filter formats to find what actually works."""
    client = _mem0_client()
    results = {}

    formats = {
        "AND_user_id":  {"AND": [{"user_id": user_id}]},
        "AND_run_id":   {"AND": [{"run_id": run_id}]},
        "flat_user_id": {"user_id": user_id},
        "flat_run_id":  {"run_id": run_id},
        "AND_both":     {"AND": [{"user_id": user_id}, {"run_id": run_id}]},
    }

    for name, f in formats.items():
        try:
            r = client.search(query=q, filters=f, limit=5)
            count = len(r.get("results", [])) if isinstance(r, dict) else len(r)
            results[name] = {"count": count, "sample": r}
        except Exception as e:
            results[name] = {"error": str(e)}

    return results