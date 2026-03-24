# File: backend/aura/agents/response_engine.py
 
import json, re
from openai import AsyncOpenAI
from aura.models import FAMResult, ECHOResult, ActionPlan, CalibrationMode
from aura.config import settings
 
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
 
# ── Medical Rule Engine ───────────────────────────────────────────────
UNSAFE_INSTRUCTIONS = [
   "apply butter", "apply toothpaste", "apply ice directly", "apply ice cubes",
   "break the blister", "pop the blister", "give food to unconscious",
   "give water to unconscious", "put fingers in mouth", "realign the bone",
   "remove object from wound", "apply heat to burn", "use rubbing alcohol on wound",
   "apply alcohol to wound", "induce vomiting without instruction",
]
 
 
def _rule_check(step: str) -> tuple[bool, str]:
   """Returns (is_safe, reason). Called for EVERY instruction step."""
   step_lower = step.lower()
   for unsafe in UNSAFE_INSTRUCTIONS:
       if unsafe in step_lower:
           return False, f"BLOCKED: {unsafe}"
   return True, "SAFE"
 
 
async def generate(
   fam: FAMResult,
   echo: ECHOResult,
   action: ActionPlan,
) -> tuple[list[str], str, int, int]:
   """Returns (safe_steps, voice_text, blocked_count, safe_count)."""
 
   # Crisis redirect — fixed response, no LLM needed
   if echo.calibration_mode == CalibrationMode.CRISIS_REDIRECT:
       steps = [
           "Please call emergency services (108 or 112) RIGHT NOW.",
           "You are not alone. Help is coming.",
           "Stay on the line with emergency services.",
       ]
       return steps, "Please call 108 immediately. You are not alone.", 0, 3
 
   # Generate draft from LLM
   draft = await _llm_draft(fam, echo.calibration_mode)
   all_steps = draft if draft else fam.protocol_steps
 
   # Rule engine validation — every step checked
   safe_steps, blocked = [], 0
   for step in all_steps:
       is_safe, reason = _rule_check(step)
       if is_safe:
           safe_steps.append(step)
       else:
           blocked += 1
           print(f"[ResponseEngine] {reason} in step: {step[:60]}")
 
   # Calibrate based on ECHO mode
   safe_steps = _calibrate(safe_steps, echo.calibration_mode)
   voice_text = _build_voice(safe_steps, echo.calibration_mode)
   return safe_steps, voice_text, blocked, len(safe_steps)
 
 
async def _llm_draft(fam: FAMResult, mode: CalibrationMode) -> list[str]:
   panic_mode = mode == CalibrationMode.FULL_REWRITE
   style = ("ultra-simple, max 10 words per step, panic conditions"
            if panic_mode else "clear professional first-aid instructions")
   flags = ", ".join(fam.personal_flags) if fam.personal_flags else "none"
   ci = ", ".join(fam.contraindications) if fam.contraindications else "none"
   n_steps = 3 if panic_mode else 5
   prompt = (
       f"You are a first-aid guidance AI.\n"
       f"Emergency: {fam.injury} on {fam.body_part or 'body'}.\n"
       f"Severity: {fam.severity.value}. Patient flags: {flags}.\n"
       f"NEVER suggest: {ci}.\n"
       f"Generate EXACTLY {n_steps} first-aid steps. Style: {style}.\n"
       f"Return ONLY a JSON array of {n_steps} strings. No markdown, no other text.\n"
       f'Example: ["Step 1 text", "Step 2 text"]'
   )
   try:
       resp = await client.chat.completions.create(
           model="gpt-4o", max_tokens=400,
           messages=[{"role": "user", "content": prompt}]
       )
       raw = re.sub(r"```json|```", "", resp.choices[0].message.content).strip()
       return json.loads(raw)
   except Exception as e:
       print(f"[ResponseEngine] LLM draft failed: {e}")
       return []
 
 
def _calibrate(steps: list[str], mode: CalibrationMode) -> list[str]:
   if mode == CalibrationMode.FULL_REWRITE:
       return steps[:3]
   if mode == CalibrationMode.HEDGE_INJECT:
       steps = steps[:5]
       steps.append("If symptoms worsen or you are unsure, call emergency services (108) immediately.")
   return steps
 
 
def _build_voice(steps: list[str], mode: CalibrationMode) -> str:
    limit = 3 if mode == CalibrationMode.FULL_REWRITE else 5
    parts = []

    for i, s in enumerate(steps[:limit], 1):
        clean_text = s.strip()

        if mode == CalibrationMode.FULL_REWRITE:
            clean_text = " ".join(clean_text.split()[:12])

        parts.append(f"Step {i}: {clean_text}.")

    return " ".join(parts)
