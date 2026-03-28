# File: backend/aura/agents/response_engine.py

import json, re
from pathlib import Path
from aura.models import FAMResult, ECHOResult, ActionPlan, CalibrationMode, TransportMode
from aura.config import settings

try:
    from openai import AsyncOpenAI
    _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception:
    _openai_client = None

UNSAFE_INSTRUCTIONS = [
    "apply butter", "apply toothpaste", "apply ice directly", "apply ice cubes",
    "break the blister", "pop the blister", "give food to unconscious",
    "give water to unconscious", "put fingers in mouth", "realign the bone",
    "remove object from wound", "apply heat to burn", "use rubbing alcohol on wound",
    "apply alcohol to wound", "induce vomiting without instruction",
]


def _rule_check(step: str) -> tuple[bool, str]:
    step_lower = step.lower()
    for unsafe in UNSAFE_INSTRUCTIONS:
        if unsafe in step_lower:
            return False, f"BLOCKED: {unsafe}"
    return True, "SAFE"


def _build_steps_from_protocol(fam: FAMResult, mode: CalibrationMode) -> list[str]:
    """
    Return protocol steps shaped for the calibration mode.
    Steps are NEVER word-truncated — full sentences always preserved.
    FULL_REWRITE limits to first 3 steps only (no mid-sentence cuts).
    """
    base = list(fam.protocol_steps)
    if not base:
        return [
            "Stay calm and keep the person still.",
            "Call emergency services (108) if unsure.",
            "Monitor breathing and consciousness.",
        ]

    if mode == CalibrationMode.FULL_REWRITE:
        # Return first 3 complete steps — no word trimming
        return base[:3]

    if mode == CalibrationMode.HEDGE_INJECT:
        steps  = base[:5]
        caveat = (
            "If symptoms worsen or you are unsure, "
            "call emergency services (108) immediately."
        )
        if not any("108" in s for s in steps):
            steps.append(caveat)
        return steps

    return base


async def _llm_draft(fam: FAMResult, mode: CalibrationMode) -> list[str]:
    panic_mode = mode == CalibrationMode.FULL_REWRITE
    style  = (
        "ultra-simple, max 10 words per step, panic conditions"
        if panic_mode else "clear professional first-aid instructions"
    )
    flags  = ", ".join(fam.personal_flags)    if fam.personal_flags    else "none"
    ci     = ", ".join(fam.contraindications) if fam.contraindications else "none"
    n_steps = 3 if panic_mode else 5

    prompt = (
        f"You are a first-aid guidance AI.\n"
        f"Emergency: {fam.injury} on {fam.body_part or 'body'}.\n"
        f"Severity: {fam.severity.value}. Patient flags: {flags}.\n"
        f"NEVER suggest: {ci}.\n"
        f"Generate EXACTLY {n_steps} first-aid steps. Style: {style}.\n"
        f"Return ONLY a JSON array of {n_steps} strings. "
        f"No markdown, no other text.\n"
        f'Example: ["Step 1 text", "Step 2 text"]'
    )
    resp = await _openai_client.chat.completions.create(
        model="gpt-4o", max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = re.sub(r"```json|```", "", resp.choices[0].message.content).strip()
    return json.loads(raw)


def _resolve_calibration_mode(
    echo: ECHOResult, action: ActionPlan
) -> CalibrationMode:
    if echo.calibration_mode == CalibrationMode.CRISIS_REDIRECT:
        return CalibrationMode.CRISIS_REDIRECT
    if action.transport == TransportMode.AMBULANCE:
        return CalibrationMode.FULL_REWRITE
    return echo.calibration_mode


def _calibrate(steps: list[str], mode: CalibrationMode) -> list[str]:
    """Limit step count per mode. No word-level truncation."""
    if mode == CalibrationMode.FULL_REWRITE:
        return steps[:3]
    if mode == CalibrationMode.HEDGE_INJECT:
        steps = steps[:5]
        caveat = (
            "If symptoms worsen or you are unsure, "
            "call emergency services (108) immediately."
        )
        if not any("108" in s for s in steps):
            steps.append(caveat)
    return steps


def _build_voice(steps: list[str], mode: CalibrationMode) -> str:
    """
    Build voice text from FULL sentences — no word trimming.
    FULL_REWRITE uses first 3 steps, others use up to 5.
    """
    limit = 3 if mode == CalibrationMode.FULL_REWRITE else 5
    parts = []
    for i, s in enumerate(steps[:limit], 1):
        parts.append(f"Step {i}: {s.strip()}.")
    return " ".join(parts)


async def generate(
    fam: FAMResult,
    echo: ECHOResult,
    action: ActionPlan,
) -> tuple[list[str], str, int, int]:
    """Returns (safe_steps, voice_text, blocked_count, safe_count)."""

    effective_mode = _resolve_calibration_mode(echo, action)

    # Crisis redirect — fixed response, no LLM
    if effective_mode == CalibrationMode.CRISIS_REDIRECT:
        steps = [
            "Please call emergency services (108 or 112) RIGHT NOW.",
            "You are not alone. Help is coming.",
            "Stay on the line with emergency services.",
        ]
        return steps, "Please call 108 immediately. You are not alone.", 0, 3

    # Try LLM, fall back to protocol steps
    draft = []
    if _openai_client and settings.OPENAI_API_KEY:
        try:
            draft = await _llm_draft(fam, effective_mode)
        except Exception as e:
            print(f"[ResponseEngine] OpenAI unavailable ({e}), "
                  f"falling back to protocol steps")

    if not draft:
        draft = _build_steps_from_protocol(fam, effective_mode)

    # Medical rule engine
    safe_steps: list[str] = []
    blocked = 0
    for step in draft:
        is_safe, reason = _rule_check(step)
        if is_safe:
            safe_steps.append(step)
        else:
            blocked += 1
            print(f"[ResponseEngine] {reason} → step: {step[:60]}")

    safe_steps = _calibrate(safe_steps, effective_mode)
    voice_text = _build_voice(safe_steps, effective_mode)

    return safe_steps, voice_text, blocked, len(safe_steps)