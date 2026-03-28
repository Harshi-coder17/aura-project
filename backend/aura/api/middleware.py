# File: backend/aura/api/middleware.py

import re
import time
from collections import defaultdict
from fastapi import Request, Response

_request_counts: dict = defaultdict(list)
RATE_LIMIT_PER_MINUTE = 20


async def rate_limit_middleware(request: Request, call_next):
    """Rate limit: 20 requests/minute per IP on /api/v1/process."""
    if request.url.path == "/api/v1/process":
        client_ip = request.client.host if request.client else "unknown"
        now       = time.time()
        window    = [t for t in _request_counts[client_ip] if now - t < 60]

        if len(window) >= RATE_LIMIT_PER_MINUTE:
            return Response(
                content='{"error":"Rate limit exceeded. Max 20 requests/minute."}',
                status_code=429,
                media_type="application/json",
            )
        _request_counts[client_ip] = window + [now]

    return await call_next(request)


def sanitize_text(text: str) -> str:
    """Remove script injection attempts and normalize input."""
    text = re.sub(r"<script.*?>.*?</script>", "", text,
                  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(.{1,20})\1{5,}", r"\1", text)
    return text[:2000].strip()