import json, uuid, asyncio
from datetime import datetime, timezone
from pathlib import Path
from aura.models import ProcessRequest, FAMResult, ECHOResult, ActionPlan

AUDIT_LOG = Path("./logs/aura_audit.jsonl")
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


async def log(
    req: ProcessRequest,
    fam: FAMResult,
    echo: ECHOResult,
    action: ActionPlan,
    response_steps: list[str],
    blocked_count: int,
    dispatch_status: str,
) -> str:
    audit_id = str(uuid.uuid4())[:8].upper()

    record = {
        "audit_id": audit_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": req.session_id,
        "user_id": req.user_id,
        "mode": getattr(req.mode, "value", req.mode),

        "turn": req.turn_number,

        "fam": {
            "injury": fam.injury,
            "severity": getattr(fam.severity, "value", fam.severity),
            "confidence": fam.confidence,
            "protocol": fam.protocol_code,
            "body_part": fam.body_part,
            "personal_flags": fam.personal_flags,
        },

        "echo": {
            "composite": echo.composite,
            "risk_level": getattr(echo.risk_level, "value", echo.risk_level),
            "ml_score": echo.ml_score,
            "rule_score": echo.rule_score,
            "context_score": echo.context_score,
            "calibration_mode": getattr(echo.calibration_mode, "value", echo.calibration_mode),
            "signals": echo.signals,
            "flag_critical": echo.flag_critical,
        },

        "decision": {
            "transport": getattr(action.transport, "value", action.transport),
            "response_mode": action.response_mode,
            "rationale": action.rationale,
            "escalate": action.escalate_to_doctor,
            "notify_contacts": action.notify_contacts,
        },

        "response": {
            "steps_count": len(response_steps),
            "blocked_count": blocked_count,
            "dispatch_status": dispatch_status,
        },
    }

    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return audit_id


def get_recent_logs(n: int = 50) -> list[dict]:
    if not AUDIT_LOG.exists():
        return []

    lines = [l for l in AUDIT_LOG.read_text().strip().split("\n") if l.strip()]
    return [json.loads(l) for l in lines[-n:]]
