# File: backend/aura/agents/fam_agent.py

import json, re
from pathlib import Path
from aura.models import FAMResult, SeverityLevel, ProcessRequest
from aura.config import settings

try:
    from openai import AsyncOpenAI
    _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception:
    _openai_client = None

PROTOCOLS_PATH = Path(__file__).parent.parent.parent / "data" / "protocols" / "protocols.json"
LEXICON_DIR    = Path(__file__).parent.parent.parent / "data" / "lexicons"

PROTOCOLS: dict = {}

MOCK_PROFILES = {
    "user_demo": {
        "conditions": ["diabetic", "hypertension"],
        "allergies":   ["aspirin", "ibuprofen"],
        "medications": ["metformin", "amlodipine"]
    },
    "user_test": {
        "conditions": ["asthmatic"],
        "allergies":   ["penicillin"],
        "medications": ["salbutamol inhaler"]
    }
}

# Condition → trigger keywords in input text that cause severity escalation
_CONDITION_ESCALATION = {
    "asthmatic":   ["breathing", "breath", "breathe", "inhale", "wheeze",
                    "chest tight", "cant breathe", "short of breath"],
    "diabetic":    ["wound", "cut", "bleeding", "burn", "burned", "infection",
                    "healing", "foot", "leg", "hand", "finger"],
    "hypertension":["chest pain", "headache", "dizzy", "faint",
                    "heart", "stroke", "vision"],
    "cardiac":     ["chest", "pain", "pressure", "heart", "arm numb"],
    "epileptic":   ["seizure", "fit", "shaking", "convulsion"],
    "allergic":    ["swelling", "throat", "rash", "hives", "anaphylaxis",
                    "bee", "sting", "nut", "peanut"],
}

# Condition → best protocol code to use when that condition is triggered
# This ensures personal mode gets the right protocol steps even if the
# input text doesn't score high enough on its own.
_CONDITION_PROTOCOL_HINT = {
    "asthmatic":    None,           # no single protocol — use matched or DEFAULT
    "diabetic":     {
        # keyword fragment → protocol code
        "burn":     "BURN_SEVERE_001",
        "wound":    "BLEEDING_001",
        "cut":      "BLEEDING_001",
        "bleeding": "BLEEDING_001",
        "foot":     "BLEEDING_001",
        "leg":      "BLEEDING_001",
        "hand":     "BURN_SEVERE_001",
        "finger":   "BLEEDING_001",
    },
    "hypertension": {
        "chest":    "CARDIAC_001",
        "heart":    "CARDIAC_001",
    },
    "cardiac":      {
        "chest":    "CARDIAC_001",
        "heart":    "CARDIAC_001",
    },
    "epileptic":    {
        "seizure":  "SEIZURE_001",
        "fit":      "SEIZURE_001",
        "shaking":  "SEIZURE_001",
    },
    "allergic":     None,
}


def _load_protocols():
    global PROTOCOLS
    if PROTOCOLS_PATH.exists():
        PROTOCOLS = json.loads(PROTOCOLS_PATH.read_text())
        print(f"[FAM] Loaded {len(PROTOCOLS)} protocols")
    else:
        print(f"[FAM] WARNING: protocols.json not found at {PROTOCOLS_PATH}")
        PROTOCOLS = {}


_load_protocols()


def _normalize_for_matching(text: str) -> str:
    """Lowercase, collapse whitespace, expand common verb forms."""
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("burned",   "burn")
    t = t.replace("burnt",    "burn")
    t = t.replace("broken",   "fracture")
    t = t.replace("choking",  "choking")
    t = t.replace("swallowed","swallowed")
    return t


def _score_protocols(text_norm: str) -> tuple[str, dict, float]:
    """Score all protocols, return (best_code, best_proto, best_score)."""
    best_code  = "DEFAULT_001"
    best_score = 0.0
    best_proto = PROTOCOLS.get("DEFAULT_001", {})

    for code, proto in PROTOCOLS.items():
        kws   = proto.get("keywords", [])
        score = sum(
            len(kw.split())
            for kw in kws
            if kw in text_norm
        )
        if score > best_score:
            best_score = score
            best_code  = code
            best_proto = proto

    return best_code, best_proto, best_score


def _extract_entities_lexicon(text: str) -> dict:
    text_norm = _normalize_for_matching(text)

    best_code, best_proto, best_score = _score_protocols(text_norm)

    proto_severity = best_proto.get("severity", "MODERATE").upper()

    body_parts = [
        "hand", "finger", "arm", "leg", "foot", "head", "neck", "back",
        "chest", "stomach", "shoulder", "knee", "ankle", "wrist", "eye",
        "ear", "nose", "mouth", "throat", "hip", "elbow"
    ]
    detected_part = next((bp for bp in body_parts if bp in text_norm), None)

    urgency_words = [
        "help", "emergency", "dying", "cant breathe", "not breathing",
        "unconscious", "hurry", "please", "now", "severe", "worse",
        "badly", "a lot", "wont stop", "heavy", "profuse", "so much"
    ]
    urgency_hit = sum(1 for w in urgency_words if w in text_norm)

    sev_map = {"MINOR": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
    rev_map = {1: "MINOR", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}
    sev_val = sev_map.get(proto_severity, 2)

    escalation_triggers = best_proto.get("escalation_triggers", [])
    always_critical     = {"always_escalate", "always_critical"}

    if any(t in always_critical for t in escalation_triggers):
        sev_val = 4
    elif any(t.replace("_", " ") in text_norm for t in escalation_triggers):
        sev_val = 4
    elif urgency_hit >= 2 and sev_val < 4:
        sev_val = min(4, sev_val + 1)

    confidence = min(1.0, 0.40 + best_score * 0.08)

    return {
        "injury":          best_proto.get("name", "Unknown Condition"),
        "body_part":       detected_part,
        "severity_text":   rev_map[sev_val],
        "confidence":      round(confidence, 2),
        "is_emergency":    sev_val >= 3,
        "_protocol_code":  best_code,
        "_proto_severity": proto_severity,
    }


async def _extract_entities_openai(text: str, image_features: dict | None) -> dict:
    img_ctx = ""
    if image_features and image_features.get("description"):
        img_ctx = (
            f"\nImage analysis: {image_features['description']},"
            f" visual severity: {image_features.get('severity', 'unknown')}"
        )
    prompt = (
        f'You are a medical triage AI. Analyze this emergency input.\n'
        f'User message: "{text}"{img_ctx}\n'
        f'Return ONLY valid JSON (no markdown, no explanation):\n'
        f'{{"injury":"brief injury name","body_part":"affected area or null",'
        f'"severity_text":"MINOR|MODERATE|HIGH|CRITICAL",'
        f'"confidence":0.0-1.0,"is_emergency":true|false}}\n'
        f'Severity: CRITICAL=life-threatening, HIGH=ER urgent, '
        f'MODERATE=doctor soon, MINOR=home care.'
    )
    resp = await _openai_client.chat.completions.create(
        model="gpt-4o", max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = re.sub(r"```json|```", "", resp.choices[0].message.content).strip()
    return json.loads(raw)


async def _extract_entities(text: str, image_features: dict | None) -> dict:
    if _openai_client and settings.OPENAI_API_KEY:
        try:
            return await _extract_entities_openai(text, image_features)
        except Exception as e:
            print(f"[FAM] OpenAI unavailable ({e}), falling back to lexicon extractor")
    return _extract_entities_lexicon(text)


def _select_protocol(entities: dict, text: str) -> tuple[str, dict]:
    pre_code = entities.get("_protocol_code")
    if pre_code and pre_code in PROTOCOLS:
        return pre_code, PROTOCOLS[pre_code]

    text_norm          = _normalize_for_matching(text)
    best_code, proto, _ = _score_protocols(text_norm)
    return best_code, PROTOCOLS.get(best_code, PROTOCOLS.get("DEFAULT_001", {}))


def _fuse_severity(entities: dict, image_features: dict | None) -> SeverityLevel:
    sev_map  = {"MINOR": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
    rev_map  = {1: "MINOR", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}
    text_val = sev_map.get(entities.get("severity_text", "MODERATE").upper(), 2)
    img_val  = text_val
    if image_features:
        img_conf = float(image_features.get("confidence", 0.0))
        if img_conf >= 0.70:
            img_val = sev_map.get(
                image_features.get("severity", "MODERATE").upper(), 2)
    return SeverityLevel(rev_map[max(text_val, img_val)])


def _apply_personal_profile(
    user_id: str,
    base_ci: list,
    text: str,
    current_severity: SeverityLevel,
    current_protocol_code: str,
) -> tuple[list, list, SeverityLevel, str]:
    """
    Load profile, inject flags/contraindications, escalate severity if
    condition is triggered. Also corrects the protocol code when the
    lexicon extractor defaulted to DEFAULT_001 but the condition+input
    clearly implies a specific protocol (e.g. diabetic + burn → BURN).

    Returns: (flags, contraindications, escalated_severity, protocol_code)
    """
    profile    = MOCK_PROFILES.get(user_id, {})
    conditions = profile.get("conditions", [])
    allergies  = profile.get("allergies", [])

    flags    = conditions + [f"allergic:{a}" for a in allergies]
    extra_ci = [f"avoid_{a}" for a in allergies]

    sev_map = {"MINOR": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
    rev_map = {1: "MINOR", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}
    sev_val = sev_map.get(current_severity.value, 2)

    text_lower       = text.lower()
    text_norm        = _normalize_for_matching(text)
    final_protocol   = current_protocol_code
    escalated        = False

    for condition in conditions:
        condition_key = condition.lower().strip()
        trigger_words = _CONDITION_ESCALATION.get(condition_key, [])

        if any(kw in text_lower or kw in text_norm for kw in trigger_words):
            # Escalate severity by 1 notch
            new_sev = min(4, sev_val + 1)
            if new_sev != sev_val:
                sev_val   = new_sev
                escalated = True
                print(
                    f"[FAM] Personal escalation: condition '{condition}' "
                    f"triggered → severity bumped to {rev_map[sev_val]}"
                )

            # Protocol correction: if we landed on DEFAULT_001 but the
            # condition+text implies a specific protocol, override it.
            if current_protocol_code == "DEFAULT_001":
                hints = _CONDITION_PROTOCOL_HINT.get(condition_key)
                if isinstance(hints, dict):
                    for kw, proto_code in hints.items():
                        if kw in text_lower or kw in text_norm:
                            if proto_code in PROTOCOLS:
                                final_protocol = proto_code
                                print(
                                    f"[FAM] Personal protocol hint: "
                                    f"'{condition}' + '{kw}' → {proto_code}"
                                )
                            break

            break  # one escalation per request

    escalated_severity = SeverityLevel(rev_map[sev_val])
    return flags, base_ci + extra_ci, escalated_severity, final_protocol


async def analyze(payload: dict, req: ProcessRequest) -> FAMResult:
    text           = payload.get("normalized_text") or payload.get("text", "")
    image_features = payload.get("image_features")

    entities = await _extract_entities(text, image_features)

    protocol_code, protocol = _select_protocol(entities, text)

    severity = _fuse_severity(entities, image_features)

    personal_flags    = []
    contraindications = list(protocol.get("contraindications", []))
    mode_val = req.mode.value if hasattr(req.mode, "value") else str(req.mode)

    if mode_val == "personal" and getattr(req, "user_id", None):
        personal_flags, contraindications, severity, protocol_code = \
            _apply_personal_profile(
                req.user_id, contraindications, text,
                severity, protocol_code
            )
        # If protocol was corrected by personal hint, reload protocol data
        protocol = PROTOCOLS.get(protocol_code, protocol)
        contraindications = list(protocol.get("contraindications", []))
        # Re-apply allergy contraindications on top of new protocol
        allergies = MOCK_PROFILES.get(req.user_id, {}).get("allergies", [])
        contraindications += [f"avoid_{a}" for a in allergies]

    return FAMResult(
        injury            = entities.get("injury", "Unknown Condition")
                            if protocol_code == entities.get("_protocol_code")
                            else protocol.get("name", entities.get("injury", "Unknown")),
        severity          = severity,
        confidence        = float(entities.get("confidence", 0.60)),
        body_part         = entities.get("body_part"),
        protocol_code     = protocol_code,
        protocol_steps    = list(protocol.get("steps", [])),
        contraindications = contraindications,
        personal_flags    = personal_flags,
    )


async def process(text: str, mode: str):
    payload = {
        "normalized_text": text.lower().strip(),
        "text":            text,
        "image_features":  None
    }

    class DummyReq:
        def __init__(self):
            self.mode    = type("obj", (), {"value": mode})()
            self.user_id = None

    result = await analyze(payload, DummyReq())
    return {
        "injury":            result.injury,
        "severity":          result.severity.value,
        "body_part":         result.body_part or "Unknown",
        "first_aid":         result.protocol_steps,
        "confidence":        result.confidence,
        "protocol_code":     result.protocol_code,
        "contraindications": result.contraindications,
        "personal_flags":    result.personal_flags,
        "protocol_steps":    result.protocol_steps,
    }