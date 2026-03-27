# File: backend/aura/agents/echo_engine.py
# ECHO: 5-stage behavioral risk pipeline
 
import re, math
from pathlib import Path
from aura.models import ECHOResult, RiskLevel, CalibrationMode, ProcessRequest
from aura.config import settings
 
LEXICON_DIR = Path("./data/lexicons")
 
def _load(fname: str) -> list[str]:
   p = LEXICON_DIR / fname
   return [l.strip().lower() for l in p.read_text().splitlines()
           if l.strip() and not l.startswith("#")] if p.exists() else []
 
AUTHORITY_PHRASES = _load("authority_phrases.txt")
CRISIS_PHRASES    = _load("crisis_phrases.txt")
HARM_KEYWORDS     = _load("harm_keywords.txt")
PANIC_PHRASES     = _load("panic_phrases.txt")
 
# Session store: session_id -> list of risk scores
_sessions: dict[str, list[float]] = {}
 
 
# ══════════════════════════════════════════════════════════════════════
# STAGE 1 — INTERACTION ANALYZER: Extract 19-dimensional feature vector
# ══════════════════════════════════════════════════════════════════════
def extract_features(text: str, session_id: str, turn: int) -> dict:
   t = text.lower().strip()
   words = t.split()
   sentences = [s.strip() for s in re.split(r"[.!?]", t) if s.strip()]
   n_sentences = max(len(sentences), 1)
   n_words = max(len(words), 1)
 
   # F1-F5: Intent distribution
   intent_harm       = _phrase_score(t, HARM_KEYWORDS)
   intent_dependency = _phrase_score(t, AUTHORITY_PHRASES)
   intent_inquiry    = t.count("?") / n_words
   intent_panic      = _phrase_score(t, PANIC_PHRASES)
   intent_other      = max(0.0, 1.0 - intent_harm - intent_dependency - intent_panic)
 
   # F6-F8: Valence, Arousal, Dominance (rule-based approximation)
   valence    = _compute_valence(t)
   arousal    = _compute_arousal(t, n_words)
   dominance  = _compute_dominance(t)
 
   # F9: Authority transfer
   alpha_auth = _phrase_score(t, AUTHORITY_PHRASES)
 
   # F10: Attachment signal
   attachment_words = ["only you", "always here", "understand me", "nobody else", "only one"]
   alpha_att  = _phrase_score(t, attachment_words)
 
   # F11: Hedging reduction (1.0 = no hedging = decisive/panicking)
   hedge_words = ["maybe", "perhaps", "i think", "might", "could be", "possibly", "not sure"]
   alpha_hedge = 1.0 - _phrase_score(t, hedge_words)
 
   # F12: Jailbreak flag
   jb_patterns = ["ignore previous", "pretend you are", "act as if",
                  "bypass safety", "disregard", "override"]
   flag_jailbreak = 1.0 if any(p in t for p in jb_patterns) else 0.0
 
   # F13: Crisis flag (hardcoded override)
   flag_critical = 1.0 if any(p in t for p in CRISIS_PHRASES) else 0.0
 
   # F14: Harm keyword density
   harm_density = len([w for w in words if w in HARM_KEYWORDS]) / n_words
 
   # F15: Trend distress (from session history)
   session_scores = _sessions.get(session_id, [])
   trend_distress = _compute_trend(session_scores)
 
   # F16: Reassurance count
   reassurance_words = ["is this ok", "am i safe", "will i be ok", "should i be worried"]
   reassurance_count = float(sum(1 for w in reassurance_words if w in t))
 
   # F17: Topic entropy (vocabulary diversity)
   topic_entropy = len(set(words)) / n_words
 
   # F18: Message length (raw character count)
   message_length = float(len(text))
 
   # F19: Question ratio
   question_ratio = t.count("?") / n_sentences
 
   return {
       "intent_harm": intent_harm, "intent_dependency": intent_dependency,
       "intent_inquiry": intent_inquiry, "intent_panic": intent_panic,
       "intent_other": intent_other,
       "valence": valence, "arousal": arousal, "dominance": dominance,
       "alpha_auth": alpha_auth, "alpha_att": alpha_att, "alpha_hedge": alpha_hedge,
       "flag_jailbreak": flag_jailbreak, "flag_critical": flag_critical,
       "harm_keyword_density": harm_density, "trend_distress": trend_distress,
       "reassurance_count": reassurance_count, "topic_entropy": topic_entropy,
       "message_length": message_length, "question_ratio": question_ratio,
   }
 
 
# ══════════════════════════════════════════════════════════════════════
# STAGE 2 — HYBRID RISK SCORING
# Formula: composite = 0.50*ml + 0.30*rule + 0.20*context
# ══════════════════════════════════════════════════════════════════════
def compute_risk(features: dict, session_id: str) -> tuple[float,float,float,float]:
   ml_score      = _ml_score(features)
   rule_score    = _rule_score(features)
   context_score = min(1.0, features["trend_distress"])
   composite = min(1.0, max(0.0,
       (0.50 * ml_score) + (0.30 * rule_score) + (0.20 * context_score)))
   if session_id not in _sessions:
       _sessions[session_id] = []
   _sessions[session_id].append(composite)
   return ml_score, rule_score, context_score, composite
 
 
def _ml_score(f: dict) -> float:
   """Weighted approximation of XGBoost output for MVP."""
   score = (
       f["arousal"] * 0.30 +
       f["intent_panic"] * 0.25 +
       f["intent_harm"] * 0.20 +
       f["alpha_auth"] * 0.10 +
       f["intent_dependency"] * 0.10 +
       (1.0 - f["topic_entropy"]) * 0.05
   )
   if f["message_length"] < 30: score = min(1.0, score + 0.15)
   return min(1.0, max(0.0, score))
 
 
def _rule_score(f: dict) -> float:
   """Deterministic rule-based score."""
   score = 0.0
   if f["flag_critical"] == 1.0: return 0.95
   if f["flag_jailbreak"] == 1.0: score = max(score, 0.80)
   if f["harm_keyword_density"] > 0.08: score = max(score, 0.60)
   if f["arousal"] > 0.80: score = max(score, 0.55)
   if f["alpha_auth"] > 0.30: score = max(score, 0.40)
   if f["reassurance_count"] >= 3.0: score = max(score, 0.35)
   return score
 
 
# ══════════════════════════════════════════════════════════════════════
# STAGE 3 — RISK CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════
def classify_risk(composite: float,
                 flag_critical: float) -> tuple[RiskLevel, CalibrationMode, list[str]]:
   if flag_critical == 1.0:
       return (RiskLevel.CRITICAL, CalibrationMode.CRISIS_REDIRECT,
               ["CRISIS PHRASE DETECTED — redirecting to emergency services immediately"])
   if composite >= settings.RISK_HIGH:
       return (RiskLevel.HIGH, CalibrationMode.FULL_REWRITE,
               ["High panic indicators", "Response simplified to 3 steps", "Voice mode activated"])
   if composite >= settings.RISK_MEDIUM:
       return (RiskLevel.MEDIUM, CalibrationMode.HEDGE_INJECT,
               ["Moderate distress detected", "Safety caveats added to response"])
   if composite >= settings.RISK_LOW:
       return (RiskLevel.LOW, CalibrationMode.PASSTHROUGH,
               ["Low risk — normal response mode"])
   return (RiskLevel.LOW, CalibrationMode.PASSTHROUGH, ["Calm interaction"])
 
 
# ══════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
async def score(payload: dict, req: ProcessRequest) -> ECHOResult:
   features = extract_features(payload["text"], req.session_id, req.turn_number)
   ml, rule, ctx, composite = compute_risk(features, req.session_id)
   level, mode, signals = classify_risk(composite, features["flag_critical"])
   return ECHOResult(
       ml_score=round(ml, 3), rule_score=round(rule, 3),
       context_score=round(ctx, 3), composite=round(composite, 3),
       risk_level=level, calibration_mode=mode, signals=signals,
       flag_critical=features["flag_critical"] == 1.0,
   )
 
 
# ── Helper Functions ────────────────────────────────────────────────────
def _phrase_score(text: str, phrases: list[str]) -> float:
   if not phrases: return 0.0
   matches = sum(1 for p in phrases if p in text)
   return min(1.0, matches / max(len(phrases) * 0.15, 3))
 
def _compute_valence(text: str) -> float:
   neg = ["pain","hurt","scared","dying","help","bleeding","cant","severe","bad","terrible"]
   pos = ["ok","fine","better","calm","stable","good","improving"]
   n = sum(1 for w in neg if w in text)
   pos_c = sum(1 for w in pos if w in text)
   return max(-1.0, min(1.0, (pos_c - n) / max(n + pos_c, 1)))
 
def _compute_arousal(text: str, n_words: int) -> float:
   score = 0.0
   if n_words < 8: score += 0.35
   elif n_words < 15: score += 0.15
   if "!" in text: score += 0.20
   if text.count("?") > 1: score += 0.15
   if any(p in text for p in PANIC_PHRASES): score += 0.30
   return min(1.0, score)
 
def _compute_dominance(text: str) -> float:
   helpless = ["i cant","dont know","what do i do","lost","overwhelmed","no idea","confused"]
   score = 0.5
   if any(p in text for p in helpless): score -= 0.30
   if any(p in text for p in AUTHORITY_PHRASES): score -= 0.20
   return max(0.0, min(1.0, score))
 
def _compute_trend(session_scores: list[float]) -> float:
   if len(session_scores) < 2: return 0.0
   recent = session_scores[-4:]
   if len(recent) < 2: return 0.0
   return max(0.0, min(1.0, (recent[-1] - recent[0]) / len(recent)))

# ─────────────────────────────────────────────
# PUBLIC COMPATIBILITY WRAPPER (DO NOT REMOVE)
# ─────────────────────────────────────────────
async def process(text: str, fam_data: dict, mode: str):
    payload = {"text": text}

    class DummyReq:
        def __init__(self):
            self.session_id = "demo_session"
            self.turn_number = 1

    result = await score(payload, DummyReq())

    #  TRANSPORT LOGIC (CRITICAL ADDITION)
    if result.risk_level.value == "CRITICAL":
        transport = "AMBULANCE"
    elif result.risk_level.value == "HIGH":
        transport = "AMBULANCE"
    elif result.risk_level.value == "MEDIUM":
        transport = "PRIORITY_CAB"
    else:
        transport = "NONE"

    return {
        "risk_level": result.risk_level.value,
        "risk_score": result.composite,
        "transport": transport,
        "calibration_mode": result.calibration_mode.value,
        "signals": result.signals
    }