# File: backend/aura/agents/fam_agent.py
 
import json, re
from pathlib import Path
from openai import AsyncOpenAI
from aura.models import FAMResult, SeverityLevel, ProcessRequest
from aura.config import settings
 
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
 
PROTOCOLS_PATH = Path("./data/protocols/protocols.json")
PROTOCOLS: dict = {}
 
# Mock user profiles (replace with DB lookup in production)
MOCK_PROFILES = {
   "user_demo": {
       "conditions": ["diabetic", "hypertension"],
       "allergies": ["aspirin", "ibuprofen"],
       "medications": ["metformin", "amlodipine"]
   },
   "user_test": {
       "conditions": ["asthmatic"],
       "allergies": ["penicillin"],
       "medications": ["salbutamol inhaler"]
   }
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
 
 
async def analyze(payload: dict, req: ProcessRequest) -> FAMResult:
   """Stage 2: Extract structured medical context from input payload."""
   text = payload["normalized_text"]
   image_features = payload.get("image_features")
 
   # Step 1: GPT-4o entity extraction
   entities = await _extract_entities(text, image_features)
 
   # Step 2: Protocol selection via keyword matching
   protocol_code, protocol = _select_protocol(entities, text)
 
   # Step 3: Severity fusion (text + image)
   severity = _fuse_severity(entities, image_features)
 
   # Step 4: Personal profile injection
   personal_flags, contraindications = [], list(protocol.get("contraindications", []))
   if req.mode.value == "personal" and req.user_id:
       personal_flags, contraindications = _apply_personal_profile(
           req.user_id, contraindications)
 
   return FAMResult(
       injury=entities.get("injury", "unknown injury"),
       severity=severity,
       confidence=float(entities.get("confidence", 0.70)),
       body_part=entities.get("body_part"),
       protocol_code=protocol_code,
       protocol_steps=list(protocol.get("steps", [])),
       contraindications=contraindications,
       personal_flags=personal_flags,
   )
 
 
async def _extract_entities(text: str, image_features: dict | None) -> dict:
   """Use GPT-4o to extract structured injury entities from text."""
   img_ctx = ""
   if image_features and image_features.get("description"):
       img_ctx = (f"\nImage analysis: {image_features['description']},"
                  f" visual severity: {image_features.get('severity', 'unknown')}")
 
   prompt = (f'You are a medical triage AI. Analyze this emergency input.\n'
             f'User message: "{text}"{img_ctx}\n'
             f'Return ONLY valid JSON (no markdown, no explanation):\n'
             f'{{"injury":"brief injury name","body_part":"affected area or null",'
             f'"severity_text":"MINOR|MODERATE|HIGH|CRITICAL",'
             f'"confidence":0.0-1.0,"is_emergency":true|false}}\n'
             f'Severity: CRITICAL=life-threatening, HIGH=ER urgent, MODERATE=doctor soon, MINOR=home care.')
 
   try:
       resp = await client.chat.completions.create(
           model="gpt-4o", max_tokens=150,
           messages=[{"role": "user", "content": prompt}]
       )
       raw = re.sub(r"```json|```", "", resp.choices[0].message.content).strip()
       return json.loads(raw)
   except Exception as e:
       print(f"[FAM] Entity extraction error: {e}")
       return {"injury": "unknown", "severity_text": "MODERATE",
               "confidence": 0.5, "is_emergency": False, "body_part": None}
 
 
def _select_protocol(entities: dict, text: str) -> tuple[str, dict]:
   """Keyword-match text against protocol library to find best protocol."""
   text_lower = text.lower()
   best_code, best_score = "DEFAULT_001", 0
   for code, protocol in PROTOCOLS.items():
       score = sum(1 for kw in protocol.get("keywords", []) if kw in text_lower)
       if score > best_score:
           best_score, best_code = score, code
   return best_code, PROTOCOLS.get(best_code, PROTOCOLS.get("DEFAULT_001", {}))
 
 
def _fuse_severity(entities: dict, image_features: dict | None) -> SeverityLevel:
   """Fuse text-derived and image-derived severity — take maximum."""
   sev_map = {"MINOR": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
   rev_map = {1: "MINOR", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}
   text_val = sev_map.get(entities.get("severity_text", "MODERATE").upper(), 2)
   img_val = text_val
   if image_features:
       img_conf = float(image_features.get("confidence", 0.0))
       if img_conf >= 0.70:
           img_val = sev_map.get(image_features.get("severity","MODERATE").upper(), 2)
   return SeverityLevel(rev_map[max(text_val, img_val)])
 
 
def _apply_personal_profile(user_id: str, base_ci: list) -> tuple[list, list]:
   """Load user profile and inject personal flags and extra contraindications."""
   profile = MOCK_PROFILES.get(user_id, {})
   flags = profile.get("conditions", []) + [f"allergic:{a}" for a in profile.get("allergies", [])]
   extra_ci = [f"avoid_{a}" for a in profile.get("allergies", [])]
   return flags, base_ci + extra_ci
