import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env
load_dotenv()

# Local imports
from aura.config import settings
from aura.database import init_db

# ── SAFE IMPORT AGENTS ───────────────────────────
try:
    from aura.agents import (
        input_processor, fam_agent, echo_engine,
        context_agent, decision_engine, response_engine,
        audit_layer, action_layer
    )
    AGENTS_READY = True
except ImportError:
    AGENTS_READY = False
    print("[WARN] AI agents not available — running in SAFE MODE")


# ── LIFECYCLE ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[AURA] Database initialized")
    print(f"[AURA] Environment: {settings.ENVIRONMENT}")
    print(f"[AURA] Agents ready: {AGENTS_READY}")
    yield
    print("[AURA] Shutting down")


app = FastAPI(
    title="AURA API",
    version="1.0.1",
    description="Autonomous Understanding & Response Agent",
    lifespan=lifespan
)

# ────────────────────────────────────────────────
# CORS (safe default)
# ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════
#  MAIN ENDPOINT (FINAL FIXED)
# ════════════════════════════════════════════════
@app.post("/api/v1/process")
async def process(request: Request):
    try:
        req = await request.json()
        print("DATA RECEIVED:", req)
    except Exception as e:
        print("JSON ERROR:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    turn_id = str(uuid.uuid4())[:8].upper()

    # ── SAFE MODE (FOR NOW)
    return {
        "session_id": req.get("session_id", "unknown"),
        "turn_id": turn_id,
        "risk_level": "LOW",
        "response_steps": [
            "Backend working 🔥",
            "Your request is being processed successfully",
            "We will now integrate AI pipeline next"
        ]
    }


# ── HEALTH CHECK ────────────────────────────────
@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "service": "AURA",
        "environment": settings.ENVIRONMENT
    }


# ── RUN SERVER ─────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)