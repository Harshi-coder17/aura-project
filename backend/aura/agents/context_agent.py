# File: backend/aura/agents/context_agent.py
 
import asyncio, math
import httpx
from aura.models import ContextResult, Hospital, ProcessRequest
from aura.config import settings
 
 
async def enrich(payload: dict, req: ProcessRequest) -> ContextResult:
   """Stage 4: Add real-world environmental context."""
   location = req.location
   hospitals, weather_factor, outbreak_active = await asyncio.gather(
       _get_hospitals(location),
       _get_weather_factor(location),
       _check_outbreak(location)
   )
   outbreak_mult = 0.40 if outbreak_active else 0.0
   context_risk  = min(1.0, 0.1 * (1 + outbreak_mult) * weather_factor)
   env_parts = [f"Weather factor: {weather_factor:.1f}x"]
   if outbreak_active:
       env_parts.append("Active disease outbreak in area")
   return ContextResult(
       context_risk=round(context_risk, 3),
       environment=" | ".join(env_parts),
       outbreak_active=outbreak_active,
       weather_factor=weather_factor,
       hospitals=hospitals,
   )
 
 
async def _get_hospitals(location: dict | None) -> list[Hospital]:
   if not location or not settings.GOOGLE_MAPS_KEY:
       return _mock_hospitals()
   lat, lon = location.get("lat", 0), location.get("lon", 0)
   try:
       async with httpx.AsyncClient(timeout=3.0) as c:
           resp = await c.get(
               "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
               params={"location": f"{lat},{lon}", "radius": 5000,
                       "type": "hospital", "key": settings.GOOGLE_MAPS_KEY}
           )
       places = resp.json().get("results", [])[:3]
   except Exception:
       return _mock_hospitals()
   hospitals = []
   for pl in places:
       loc = pl.get("geometry", {}).get("location", {})
       dist = _haversine(lat, lon, loc.get("lat", lat), loc.get("lng", lon))
       hospitals.append(Hospital(
           name=pl.get("name", "Hospital"),
           distance_km=round(dist, 1),
           eta_minutes=int(dist * 3 + 5),
           address=pl.get("vicinity", ""),
           capability=["emergency"],
       ))
   return hospitals or _mock_hospitals()
 
 
async def _get_weather_factor(location: dict | None) -> float:
   """MVP: returns 1.0. Production: call OpenWeatherMap free API."""
   return 1.0
 
 
async def _check_outbreak(location: dict | None) -> bool:
   """MVP: returns False. Production: query WHO/IDSP disease alert API."""
   return False
 
 
def _mock_hospitals() -> list[Hospital]:
   return [
       Hospital(name="City General Hospital", distance_km=1.5, eta_minutes=8,
                address="123 Main Street", phone="108",
                capability=["emergency", "trauma"]),
       Hospital(name="Apollo Hospital", distance_km=2.8, eta_minutes=12,
                address="456 Park Road", phone="1066",
                capability=["emergency", "cardiac", "burns"]),
       Hospital(name="Community Medical Center", distance_km=4.1, eta_minutes=18,
                address="789 Lake View", phone="102",
                capability=["emergency"]),
   ]
 
 
def _haversine(lat1, lon1, lat2, lon2) -> float:
   R = 6371
   dlat = math.radians(lat2 - lat1)
   dlon = math.radians(lon2 - lon1)
   a = (math.sin(dlat/2)**2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
   return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
 