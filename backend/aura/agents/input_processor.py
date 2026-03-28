# File: backend/aura/agents/input_processor.py

import re
import json
from aura.models import ProcessRequest
from aura.config import settings

# ── Optional OpenAI import ────────────────────────────────────────────
try:
    from openai import AsyncOpenAI
    _openai_client = (
        AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        if settings.OPENAI_API_KEY else None
    )
except Exception:
    _openai_client = None


async def process_input(req: ProcessRequest) -> dict:
    """Stage 1: Convert multimodal input to unified structured payload."""
    result = {
        "text":            req.text.strip(),
        "normalized_text": _normalize_text(req.text),
        "language":        req.language,
        "image_features":  None,
        "location":        req.location,
        "input_mode":      "text",
    }
    if req.image_url:
        result["input_mode"]     = "text+image"
        result["image_features"] = await _analyze_image(req.image_url)
    return result


async def _analyze_image(image_url: str) -> dict:
    """
    Call GPT-4o Vision to analyze injury from image.
    Falls back to a neutral unknown dict if OpenAI is unavailable.
    """
    if not _openai_client:
        print("[InputProcessor] OpenAI not configured — skipping image analysis")
        return _image_fallback()

    try:
        resp = await _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": (
                    "Analyze this image for a medical emergency. "
                    "Return ONLY valid JSON: "
                    '{"injury_class":"description",'
                    '"severity":"MINOR|MODERATE|HIGH|CRITICAL",'
                    '"body_part":"affected part",'
                    '"confidence":0.0-1.0,'
                    '"description":"brief"} '
                    "Severity: CRITICAL=life-threatening, "
                    "HIGH=ER needed, MODERATE=doctor, MINOR=home."
                )}
            ]}],
            max_tokens=200
        )
        raw = re.sub(
            r"```json|```", "",
            resp.choices[0].message.content
        ).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[InputProcessor] Image analysis error: {e}")
        return _image_fallback()


def _image_fallback() -> dict:
    return {
        "injury_class": "unknown",
        "severity":     "MODERATE",
        "confidence":   0.3,
        "body_part":    "unknown",
        "description":  "",
    }


def _normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+",    " ",  text)
    text = re.sub(r"[!]{2,}", "!", text)
    text = re.sub(r"[?]{2,}", "?", text)
    return text