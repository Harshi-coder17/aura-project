# File: backend/aura/agents/decision_engine.py

from aura.models import (
    FAMResult, ECHOResult, ContextResult, ActionPlan,
    RiskLevel, SeverityLevel, TransportMode, ProcessRequest
)

# Protocols where ANY presentation requires ambulance (inherently life-threatening)
_ALWAYS_AMBULANCE_PROTOCOLS = {
    "CARDIAC_001",
    "CHOKING_ADULT_001",
    "POISONING_001",
    "SEIZURE_001",
}

# Protocols requiring minimum Priority Cab for HIGH severity,
# BUT ambulance if severity reaches CRITICAL (e.g. via personal escalation)
_MINIMUM_CAB_PROTOCOLS = {
    "BLEEDING_001",
    "BURN_SEVERE_001",
    "FRACTURE_001",
}


async def decide(
    fam: FAMResult,
    echo: ECHOResult,
    ctx: ContextResult,
    req: ProcessRequest,
) -> ActionPlan:
    """Stage 5: Synthesize all agent outputs into one action plan."""

    hospital = ctx.hospitals[0] if ctx.hospitals else None

    # OVERRIDE 1: Crisis phrase → ambulance
    if echo.flag_critical:
        return ActionPlan(
            transport          = TransportMode.AMBULANCE,
            response_mode      = "CRISIS_REDIRECT",
            hospital           = hospital,
            escalate_to_doctor = True,
            notify_contacts    = True,
            rationale          = "CRISIS_OVERRIDE: Critical phrase detected",
        )

    # OVERRIDE 2: Inherently life-threatening protocol → ambulance always
    if fam.protocol_code in _ALWAYS_AMBULANCE_PROTOCOLS:
        return ActionPlan(
            transport          = TransportMode.AMBULANCE,
            response_mode      = "VOICE_3STEP",
            hospital           = hospital,
            escalate_to_doctor = True,
            notify_contacts    = True,
            rationale          = (
                f"MEDICAL_OVERRIDE: Protocol {fam.protocol_code} always "
                f"requires ambulance. Severity={fam.severity.value}, "
                f"ECHO composite={echo.composite:.2f}"
            ),
        )

    # OVERRIDE 3: CRITICAL severity → always ambulance regardless of protocol
    # This catches personal-escalated cases (e.g. diabetic + bleeding → CRITICAL)
    if fam.severity == SeverityLevel.CRITICAL:
        return ActionPlan(
            transport          = TransportMode.AMBULANCE,
            response_mode      = "VOICE_ONLY_3STEP",
            hospital           = hospital,
            escalate_to_doctor = True,
            notify_contacts    = True,
            rationale          = (
                f"SEVERITY_OVERRIDE: CRITICAL severity always requires ambulance. "
                f"Protocol={fam.protocol_code}, "
                f"ECHO composite={echo.composite:.2f}"
            ),
        )

    # OVERRIDE 4: Minimum-cab protocols at HIGH severity
    # → Priority Cab baseline, but show both buttons on frontend
    if (fam.protocol_code in _MINIMUM_CAB_PROTOCOLS and
            fam.severity == SeverityLevel.HIGH):
        return ActionPlan(
            transport          = TransportMode.PRIORITY_CAB,
            response_mode      = "FULL_PROTOCOL",
            hospital           = hospital,
            escalate_to_doctor = True,
            notify_contacts    = True,
            rationale          = (
                f"INJURY_OVERRIDE: {fam.protocol_code} HIGH severity → "
                f"Priority Cab minimum. ECHO={echo.risk_level.value}"
            ),
        )

    # Standard decision matrix
    transport, response_mode = _matrix(fam.severity, echo.risk_level)

    if ctx.outbreak_active and transport == TransportMode.SELF:
        transport = TransportMode.PRIORITY_CAB

    escalate = fam.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
    notify   = escalate or echo.composite > 0.70

    return ActionPlan(
        transport          = transport,
        response_mode      = response_mode,
        hospital           = hospital,
        escalate_to_doctor = escalate,
        notify_contacts    = notify,
        rationale          = (
            f"Severity={fam.severity.value}, "
            f"RiskLevel={echo.risk_level.value}, "
            f"Composite={echo.composite:.2f}, "
            f"Transport={transport.value}"
        ),
    )


def _matrix(sev: SeverityLevel, risk: RiskLevel) -> tuple[TransportMode, str]:
    if sev == SeverityLevel.CRITICAL:
        return TransportMode.AMBULANCE,    "VOICE_ONLY_3STEP"
    if sev == SeverityLevel.HIGH and risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        return TransportMode.AMBULANCE,    "VOICE_3STEP"
    if sev == SeverityLevel.HIGH and risk in [RiskLevel.LOW, RiskLevel.MEDIUM]:
        return TransportMode.PRIORITY_CAB, "FULL_PROTOCOL"
    if sev == SeverityLevel.MODERATE and risk == RiskLevel.HIGH:
        return TransportMode.PRIORITY_CAB, "SIMPLIFIED_5STEP"
    if sev == SeverityLevel.MODERATE and risk in [RiskLevel.LOW, RiskLevel.MEDIUM]:
        return TransportMode.SELF,         "FULL_PROTOCOL"
    return TransportMode.NONE, "FULL_PROTOCOL"