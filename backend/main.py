import uuid, sys, os 
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from aura.models import ProcessRequest, ProcessResponse
from aura.config import settings
from aura.database import init_db
from aura.api.middleware import rate_limit_middleware
from aura.agents import audit_layer, action_layer

# ── Agent imports (safe loading) ───────────────────────────
try:
    from aura.agents import (
        input_processor, fam_agent, echo_engine,
        context_agent, decision_engine, response_engine
    )
    AGENTS_READY = True
except ImportError:
    AGENTS_READY = False
    print("[WARN] AI agents not available — running in SAFE MODE")


# ── App lifecycle ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"[AURA] Database initialized")
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


# ── Middleware ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)


# ══════════════════════════════════════════════════════════
# MAIN PIPELINE ENDPOINT
# ══════════════════════════════════════════════════════════
@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(req: ProcessRequest) -> ProcessResponse:
    turn_id = str(uuid.uuid4())[:8].upper()

    # ── SAFE MODE ─────────────────────────────────────────
    if not AGENTS_READY:
        return ProcessResponse(
            session_id=req.session_id,
            turn_id=turn_id,
            risk_level="LOW",
            risk_score=0.0,
            fam_result={
                "injury": "unknown",
                "severity": "MODERATE",
                "confidence": 0.5,
                "protocol_code": "DEFAULT_001",
                "protocol_steps": ["System initializing"],
                "contraindications": [],
                "personal_flags": []
            },
            echo_result={
                "ml_score": 0.0,
                "rule_score": 0.0,
                "context_score": 0.0,
                "composite": 0.0,
                "risk_level": "LOW",
                "calibration_mode": "PASSTHROUGH",
                "signals": [],
                "flag_critical": False
            },
            action_plan={
                "transport": "NONE",
                "response_mode": "basic",
                "hospital": None,
                "escalate_to_doctor": False,
                "notify_contacts": False,
                "rationale": "Agents not ready"
            },
            response_steps=["System warming up. Try again shortly."],
            voice_text="System is initializing",
            dispatch_status="NONE",
            audit_id="SAFE0000"
        )

    # ── NORMAL PIPELINE ────────────────────────────────────
    try:
        payload = await input_processor.process_input(req)

        fam_result = await fam_agent.analyze(payload, req)
        echo_result = await echo_engine.score(payload, req)
        ctx_result = await context_agent.enrich(payload, req)

        action_plan = await decision_engine.decide(
            fam_result, echo_result, ctx_result, req
        )

        steps, voice_text, blocked, safe = await response_engine.generate(
            fam_result, echo_result, action_plan
        )

        dispatch_result = await action_layer.execute(
            action_plan, req.session_id, req.location
        ) or {}

        audit_id = await audit_layer.log(
            req, fam_result, echo_result, action_plan,
            steps, blocked,
            dispatch_result.get("dispatch_status", "NONE")
        )

        return ProcessResponse(
            session_id=req.session_id,
            turn_id=turn_id,
            risk_level=echo_result.risk_level,
            risk_score=echo_result.composite,
            fam_result=fam_result,
            echo_result=echo_result,
            action_plan=action_plan,
            response_steps=steps,
            voice_text=voice_text,
            dispatch_status=dispatch_result.get("dispatch_status", "NONE"),
            audit_id=audit_id,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Supporting Endpoints ─────────────────────────────────
@app.post("/api/v1/session/start")
async def start_session():
    return {"session_id": str(uuid.uuid4()), "status": "ok"}


@app.get("/api/v1/hospitals")
async def get_hospitals(lat: float = 0.0, lon: float = 0.0):
    if AGENTS_READY:
        from aura.models import ProcessRequest, UserMode  # restored as requested
        hospitals = await context_agent._get_hospitals({"lat": lat, "lon": lon})
        return {"hospitals": [h.model_dump() for h in hospitals]}
    return {"hospitals": []}


@app.get("/api/v1/audit")
async def get_audit(limit: int = 50):
    return {"logs": audit_layer.get_recent_logs(limit)}


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "service": "AURA",
        "version": "1.0.1",
        "agents_ready": AGENTS_READY,
        "environment": settings.ENVIRONMENT
    }


# ── Run Server ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 