from aura.agents.fam_agent import analyze
from aura.agents.echo_engine import score
from aura.agents.context_agent import enrich
from aura.agents.decision_engine import decide
from aura.agents.response_engine import generate

from aura.models import ProcessRequest
import asyncio

req = ProcessRequest(
    session_id="test123",
    text="I am bleeding badly please help me I am panicking what do I do",
    language="en",
    location={"lat": 28.6, "lon": 77.2},
    image_url=None,
    user_id=None,
    mode="stranger",
    turn_number=1
)

async def run_pipeline():
    payload = {
        "normalized_text": req.text.lower(),
        "text": req.text,
        "image_features": None
    }

    fam = await analyze(payload, req)
    echo = await score({"text": req.text}, req)
    ctx = await enrich(payload, req)
    action = await decide(fam, echo, ctx, req)
    response = await generate(fam, echo, action)

    return fam, echo, ctx, action, response


if __name__ == "__main__":
    result = asyncio.run(run_pipeline())
    print(result)