# File: backend/main.py

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from aura.config import settings
from aura.database import init_db
from aura.models import (
    ProcessRequest, UserMode,
    FAMResult, ECHOResult, ActionPlan,
    SeverityLevel, CalibrationMode, TransportMode
)
from aura.api.middleware import rate_limit_middleware

try:
    from aura.agents import (
        input_processor, fam_agent, echo_engine,
        context_agent, decision_engine, response_engine,
        audit_layer, action_layer
    )
    AGENTS_READY = True
except ImportError as e:
    AGENTS_READY = False
    print(f"[WARN] AI agents not available — running in SAFE MODE: {e}")


class RawProcessRequest(BaseModel):
    text: str
    mode: str = "stranger"
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    location: Optional[Dict[str, float]] = None
    image_url: Optional[str] = None
    turn_number: int = 1
    user_id: Optional[str] = None


class ProcessResponseOut(BaseModel):
    session_id: str
    turn_id: str
    risk_level: str
    risk_score: float
    response_steps: List[str]
    action_plan: Dict[str, Any]
    fam_result: Dict[str, Any]
    echo_result: Dict[str, Any]
    voice_text: str
    dispatch_status: str = "NONE"
    audit_id: str


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)


def _build_typed_request(raw: RawProcessRequest) -> ProcessRequest:
    mode_str = (raw.mode or "stranger").lower().strip()
    try:
        mode_enum = UserMode(mode_str)
    except ValueError:
        mode_enum = UserMode.STRANGER
    return ProcessRequest(
        session_id  = raw.session_id or str(uuid.uuid4()),
        user_id     = raw.user_id,
        mode        = mode_enum,
        text        = raw.text.strip(),
        image_url   = raw.image_url,
        location    = raw.location,
        language    = raw.language or "en",
        turn_number = raw.turn_number,
    )


def _fuse_display_risk(fam: FAMResult, echo: ECHOResult) -> tuple[str, float]:
    """
    FAM severity sets the floor; ECHO can push it higher.
    CRITICAL/HIGH FAM → never display LOW.
    """
    fam_sev    = fam.severity.value
    echo_level = echo.risk_level.value
    echo_score = echo.composite

    if fam_sev == "CRITICAL":
        return "CRITICAL", max(echo_score, 0.90)
    if fam_sev == "HIGH":
        if echo_level in ("HIGH", "CRITICAL"):
            return echo_level, echo_score
        return "MEDIUM", max(echo_score, 0.55)
    if fam_sev == "MODERATE":
        if echo_level in ("HIGH", "CRITICAL"):
            return echo_level, echo_score
        if echo_level == "MEDIUM":
            return "MEDIUM", echo_score
        return "MEDIUM", max(echo_score, 0.42)
    # MINOR — pure ECHO
    return echo_level, echo_score


def _get_effective_calibration(
    echo: ECHOResult, action: ActionPlan
) -> str:
    """
    The calibration mode that response_engine actually used.
    This is what the frontend should display and what tests should assert.
    """
    if echo.calibration_mode == CalibrationMode.CRISIS_REDIRECT:
        return "CRISIS_REDIRECT"
    if action.transport == TransportMode.AMBULANCE:
        return "FULL_REWRITE"
    return echo.calibration_mode.value


@app.post("/api/v1/process", response_model=ProcessResponseOut)
async def process(raw: RawProcessRequest):

    if not AGENTS_READY:
        raise HTTPException(status_code=503, detail="AI agents not yet initialized.")

    if not raw.text or not raw.text.strip():
        raise HTTPException(status_code=400, detail="text field cannot be empty")

    turn_id = str(uuid.uuid4())[:8].upper()
    req     = _build_typed_request(raw)

    try:
        payload     = await input_processor.process_input(req)
        fam_result  = await fam_agent.analyze(payload, req)
        echo_result = await echo_engine.score(payload, req)
        ctx_result  = await context_agent.enrich(payload, req)
        action_plan = await decision_engine.decide(fam_result, echo_result, ctx_result, req)

        steps, voice_text, blocked, safe = await response_engine.generate(
            fam_result, echo_result, action_plan
        )

        dispatch_result = await action_layer.execute(
            action_plan, req.session_id, req.location
        )

        audit_id = await audit_layer.log(
            req, fam_result, echo_result, action_plan,
            steps, blocked,
            dispatch_result.get("dispatch_status", "NONE")
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    # Effective calibration mode (what response_engine actually used)
    effective_cal = _get_effective_calibration(echo_result, action_plan)

    fam_dict = {
        "injury":            fam_result.injury,
        "severity":          fam_result.severity.value,
        "confidence":        fam_result.confidence,
        "body_part":         fam_result.body_part,
        "protocol_code":     fam_result.protocol_code,
        "protocol_steps":    fam_result.protocol_steps,
        "contraindications": fam_result.contraindications,
        "personal_flags":    fam_result.personal_flags,
    }

    echo_dict = {
        "risk_level":        echo_result.risk_level.value,
        "risk_score":        echo_result.composite,
        # Return the EFFECTIVE calibration mode, not raw ECHO value
        "calibration_mode":  effective_cal,
        "signals":           echo_result.signals,
        "ml_score":          echo_result.ml_score,
        "rule_score":        echo_result.rule_score,
        "context_score":     echo_result.context_score,
        "flag_critical":     echo_result.flag_critical,
    }

    action_dict = {
        "transport":          action_plan.transport.value,
        "response_mode":      action_plan.response_mode,
        "escalate_to_doctor": action_plan.escalate_to_doctor,
        "notify_contacts":    action_plan.notify_contacts,
        "rationale":          action_plan.rationale,
        "hospital": (
            {
                "name":        action_plan.hospital.name,
                "distance_km": action_plan.hospital.distance_km,
                "eta_minutes": action_plan.hospital.eta_minutes,
                "address":     action_plan.hospital.address,
                "phone":       action_plan.hospital.phone,
                "capability":  action_plan.hospital.capability,
            }
            if action_plan.hospital else None
        ),
    }

    display_risk_level, display_risk_score = _fuse_display_risk(fam_result, echo_result)

    return ProcessResponseOut(
        session_id      = req.session_id,
        turn_id         = turn_id,
        risk_level      = display_risk_level,
        risk_score      = display_risk_score,
        response_steps  = steps,
        action_plan     = action_dict,
        fam_result      = fam_dict,
        echo_result     = echo_dict,
        voice_text      = voice_text,
        dispatch_status = dispatch_result.get("dispatch_status", "NONE"),
        audit_id        = audit_id,
    )


@app.post("/api/v1/session/start")
async def start_session():
    return {"session_id": str(uuid.uuid4()), "status": "ok"}


@app.get("/api/v1/hospitals")
async def get_hospitals(lat: float = 0.0, lon: float = 0.0):
    if AGENTS_READY:
        hospitals = await context_agent._get_hospitals(
            {"lat": lat, "lon": lon} if (lat or lon) else None
        )
        return {
            "hospitals": [
                h.model_dump() if hasattr(h, "model_dump") else h.dict()
                for h in hospitals
            ]
        }
    return {"hospitals": []}


@app.get("/api/v1/audit")
async def get_audit(limit: int = 50):
    return {"logs": audit_layer.get_recent_logs(limit)}


@app.get("/api/v1/health")
async def health():
    return {
        "status":       "ok",
        "service":      "AURA",
        "version":      settings.VERSION,
        "agents_ready": AGENTS_READY,
        "environment":  settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)