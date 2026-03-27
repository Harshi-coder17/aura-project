import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel   
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any  


# Load env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

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


# ────────────────────────────────────────────────
#  REQUEST MODEL 
# ────────────────────────────────────────────────
class ProcessRequest(BaseModel):
    text: str
    mode: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    location: Optional[str] = None
    image_url: Optional[str] = None
    turn_number: int = 1

# ────────────────────────────────────────────────
#  RESPONSE MODEL
# ────────────────────────────────────────────────
class ProcessResponse(BaseModel):
    session_id: str
    turn_id: str
    risk_level: str
    risk_score: float
    response_steps: List[str]
    action_plan: Dict[str, Any]
    fam_result: Dict[str, Any]
    echo_result: Dict[str, Any]
    voice_text: str


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
#  MAIN ENDPOINT 
# ════════════════════════════════════════════════
@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(data: ProcessRequest):

    try:
        req = data.dict()
        print(" DATA RECEIVED:", req)
    except Exception as e:
        print("❌ JSON ERROR:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    turn_id = str(uuid.uuid4())[:8].upper()

    # ─────────────────────────────────────────────
    #  INPUT EXTRACTION
    # ─────────────────────────────────────────────
    text = req.get("text", "").strip()
    mode = req.get("mode", "UNKNOWN")
    session_id = req.get("session_id", "unknown")
    payload = await input_processor.process_input(data)
    # ─────────────────────────────────────────────
    #  AGENT EXECUTION PIPELINE
    # ─────────────────────────────────────────────
    fam_output = await fam_agent.analyze(payload, data)

    # convert to dict (important)
    fam_result = fam_output.dict()
   
    echo_output = await echo_engine.score(payload, data)

    echo_result = {
        "risk_level": echo_output.risk_level.value,
        "risk_score": echo_output.composite,
        "calibration_mode": echo_output.calibration_mode.value,
        "signals": echo_output.signals
    }

    # ─────────────────────────────────────────────
    #  SAFE FALLBACK (ONLY IF AGENTS FAIL)
    # ─────────────────────────────────────────────
    if not fam_result:
        fam_result = {
            "injury": "Preliminary Classification",
            "severity": "LOW",
            "body_part": "Undetermined",
            "first_aid": [],
            "personal_flags": []
        }

    if not echo_result:
        echo_result = {
            "risk_level": "LOW",
            "risk_score": 0.35,
            "transport": "NONE",
            "calibration_mode": mode
        }

    # ─────────────────────────────────────────────
    #  RISK FUSION (FAM + ECHO)  
    # ─────────────────────────────────────────────
    fam_severity = fam_result.get("severity", "LOW")

    # Normalize (important if enum/string mix)
    if isinstance(fam_severity, str):
        fam_severity = fam_severity.upper()

    #  MEDICAL OVERRIDE
    if fam_severity in ["CRITICAL", "HIGH"]:
        risk_level = "HIGH"
        risk_score = max(echo_result.get("risk_score", 0.5), 0.85)
        transport = "AMBULANCE"

    elif fam_severity == "MODERATE":
        risk_level = "MEDIUM"
        risk_score = max(echo_result.get("risk_score", 0.4), 0.6)
        transport = "PRIORITY_CAB"

    else:
        # fallback to behavioral model (ECHO)
        risk_level = echo_result.get("risk_level", "LOW")
        risk_score = echo_result.get("risk_score", 0.35)
        transport = echo_result.get("transport", "NONE")

    # ─────────────────────────────────────────────
    #  DYNAMIC RESPONSE STEPS 
    # ─────────────────────────────────────────────
    steps = []

    # Step 1: Input awareness
    steps.append(f"Input received: '{text}'")

    # Step 2: Mode
    steps.append(f"Operating mode: {mode}")

    # Step 3: Session tracking
    steps.append(f"Session trace ID: {session_id[:8]}")

    # Step 4: FAM RESULT
    if fam_result.get("injury"):
        steps.append(f"Detected condition: {fam_result['injury']}")

    if fam_result.get("body_part"):
        steps.append(f"Affected area: {fam_result['body_part']}")

    # Step 5+: FIRST AID (CORE FROM FAM)
    first_aid_steps = fam_result.get("protocol_steps", [])
    for step in first_aid_steps:
        steps.append(step)

    # Step N: Risk evaluation (ECHO)
    steps.append(f"Risk assessment → {risk_level} ({int(risk_score * 100)}%)")

    # Step N+1: Decision (ECHO)
    if transport == "AMBULANCE":
        steps.append("Emergency response required → Call ambulance immediately")
    elif transport == "PRIORITY_CAB":
        steps.append("Urgent condition → Reach nearest hospital quickly")
    else:
        steps.append("Condition stable → Monitor and follow precautions")

    # ─────────────────────────────────────────────
    #  FINAL RESPONSE
    # ─────────────────────────────────────────────
    return {
        "session_id": session_id,
        "turn_id": turn_id,

        "risk_level": risk_level,
        "risk_score": risk_score,

        "response_steps": steps,

        "action_plan": {
            "transport": transport
        },

        "fam_result": fam_result,
        "echo_result": echo_result,

        "voice_text": (
            f"Detected {fam_result.get('injury', 'condition')}. "
            f"Risk level {risk_level}. "
            + (
                "Immediate emergency assistance required."
                if transport == "AMBULANCE"
                else "Follow the recommended first aid steps."
            )
        )
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

    print("DB URL:", settings.DATABASE_URL)