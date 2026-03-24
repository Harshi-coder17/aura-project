# File: backend/aura/agents/decision_engine.py
 
from aura.models import (
   FAMResult, ECHOResult, ContextResult, ActionPlan,
   RiskLevel, SeverityLevel, TransportMode, ProcessRequest
)
 
 
async def decide(fam: FAMResult, echo: ECHOResult,
                ctx: ContextResult, req: ProcessRequest) -> ActionPlan:
   """Stage 5: Synthesize all agent outputs into one action plan."""
 
   # ── SAFETY OVERRIDE: Crisis always redirects immediately ───────────
   if echo.flag_critical:
       return ActionPlan(
           transport=TransportMode.AMBULANCE,
           response_mode="CRISIS_REDIRECT",
           hospital=ctx.hospitals[0] if ctx.hospitals else None,
           escalate_to_doctor=True,
           notify_contacts=True,
           rationale="CRISIS_OVERRIDE: Critical phrase detected",
       )
 
   # ── Decision Matrix ────────────────────────────────────────────────
   transport, response_mode = _matrix(fam.severity, echo.risk_level)
 
   # Context modifier: active outbreak upgrades self-transport to cab
   if ctx.outbreak_active and transport == TransportMode.SELF:
       transport = TransportMode.PRIORITY_CAB
 
   hospital = ctx.hospitals[0] if ctx.hospitals else None
   escalate = fam.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
   notify   = escalate or echo.composite > 0.70
 
   return ActionPlan(
       transport=transport,
       response_mode=response_mode,
       hospital=hospital,
       escalate_to_doctor=escalate,
       notify_contacts=notify,
       rationale=(
           f"Severity={fam.severity.value}, RiskLevel={echo.risk_level.value}, "
           f"Composite={echo.composite:.2f}, Transport={transport.value}"
       ),
   )
 
 
def _matrix(sev: SeverityLevel, risk: RiskLevel) -> tuple[TransportMode, str]:
   """AURA decision matrix — exactly as defined in blueprint."""
   if sev == SeverityLevel.CRITICAL:
       return TransportMode.AMBULANCE, "VOICE_ONLY_3STEP"
   if sev == SeverityLevel.HIGH and risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
       return TransportMode.AMBULANCE, "VOICE_3STEP"
   if sev == SeverityLevel.HIGH and risk in [RiskLevel.LOW, RiskLevel.MEDIUM]:
       return TransportMode.PRIORITY_CAB, "FULL_PROTOCOL"
   if sev == SeverityLevel.MODERATE and risk == RiskLevel.HIGH:
       return TransportMode.PRIORITY_CAB, "SIMPLIFIED_5STEP"
   if sev == SeverityLevel.MODERATE and risk in [RiskLevel.LOW, RiskLevel.MEDIUM]:
       return TransportMode.SELF, "FULL_PROTOCOL"
   return TransportMode.NONE, "FULL_PROTOCOL"  # MINOR
 