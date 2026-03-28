# File: backend/aura/agents/action_layer.py

import time
from aura.models import ActionPlan, TransportMode

# In-memory dispatch log for MVP (used later by audit_layer)
_dispatch_log: list[dict] = []


async def execute(
    action: ActionPlan,
    session_id: str,
    location: dict | None,
) -> dict:

    # DO NOT change these keys — used by main.py and audit_layer
    results = {
        "session_id":      session_id,
        "actions_taken":   [],
        "dispatch_status": "NONE",
        "dispatch_ref":    None,
    }

    # Ambulance case
    if action.transport == TransportMode.AMBULANCE:
        ref = await _dispatch_ambulance(session_id, location, action.hospital)
        results["dispatch_ref"]    = ref
        results["dispatch_status"] = "DISPATCHED"
        results["actions_taken"].append("AMBULANCE_DISPATCHED")
        results["eta_minutes"] = getattr(action.hospital, "eta_minutes", 10)

    # Cab case
    elif action.transport == TransportMode.PRIORITY_CAB:
        ref = await _book_cab(session_id, location, action.hospital)
        results["dispatch_ref"]    = ref
        results["dispatch_status"] = "CAB_BOOKED"
        results["actions_taken"].append("CAB_BOOKED")

    # Notify contacts (independent of transport type)
    if action.notify_contacts:
        await _notify_contacts(session_id, location)
        results["actions_taken"].append("CONTACTS_NOTIFIED")

    return results


async def _dispatch_ambulance(session_id, location, hospital) -> str:
    ref = f"AMB-{session_id[:6].upper()}-{int(time.time()) % 10000}"
    _dispatch_log.append({
        "ref":        ref,
        "type":       "AMBULANCE",
        "session_id": session_id,
        "location":   location,
        "hospital":   getattr(hospital, "name", "Nearest ER"),
        "status":     "DISPATCHED",
        "timestamp":  time.time(),
    })
    print(f"[ACTION] Ambulance dispatched: {ref}")
    return ref


async def _book_cab(session_id, location, hospital) -> str:
    ref = f"CAB-{session_id[:6].upper()}-{int(time.time()) % 10000}"
    _dispatch_log.append({
        "ref":        ref,
        "type":       "CAB",
        "session_id": session_id,
        "location":   location,
        "hospital":   getattr(hospital, "name", "Hospital"),
        "timestamp":  time.time(),
    })
    print(f"[ACTION] Priority cab booked: {ref}")
    return ref


async def _notify_contacts(session_id, location):
    print(f"[ACTION] Emergency contacts notified for {session_id}")
    # Production: Twilio SMS API
    # client = twilio.rest.Client(ACCOUNT_SID, AUTH_TOKEN)
    # client.messages.create(to=phone, from_=TWILIO_NUMBER, body=msg)