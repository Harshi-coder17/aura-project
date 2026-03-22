from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class UserMode(str, Enum):
    PERSONAL = "personal"
    STRANGER = "stranger"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CalibrationMode(str, Enum):
    PASSTHROUGH = "PASSTHROUGH"
    HEDGE_INJECT = "HEDGE_INJECT"
    FULL_REWRITE = "FULL_REWRITE"
    CRISIS_REDIRECT = "CRISIS_REDIRECT"


class TransportMode(str, Enum):
    AMBULANCE = "AMBULANCE"
    PRIORITY_CAB = "PRIORITY_CAB"
    SELF = "SELF"
    NONE = "NONE"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


class ProcessRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    mode: UserMode = UserMode.STRANGER
    text: str = Field(..., min_length=1, max_length=2000)
    image_url: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    language: str = "en"
    turn_number: int = 1


class FAMResult(BaseModel):
    injury: str
    severity: SeverityLevel
    confidence: float
    body_part: Optional[str] = None
    protocol_code: str
    protocol_steps: List[str]
    contraindications: List[str] = []
    personal_flags: List[str] = []


class ECHOResult(BaseModel):
    ml_score: float
    rule_score: float
    context_score: float
    composite: float
    risk_level: RiskLevel
    calibration_mode: CalibrationMode
    signals: List[str]
    flag_critical: bool = False


class Hospital(BaseModel):
    name: str
    distance_km: float
    eta_minutes: int
    address: str
    phone: Optional[str] = None
    capability: List[str] = []


class ContextResult(BaseModel):
    context_risk: float
    environment: str
    outbreak_active: bool = False
    weather_factor: float = 1.0
    hospitals: List[Hospital] = []


class ActionPlan(BaseModel):
    transport: TransportMode
    response_mode: str
    hospital: Optional[Hospital] = None
    escalate_to_doctor: bool = False
    notify_contacts: bool = False
    rationale: str


class UserProfile(BaseModel):
    user_id: str
    name: str = "User"
    age: Optional[int] = None
    blood_group: Optional[str] = None
    conditions: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    emergency_contacts: List[Dict[str, str]] = []


class ProcessResponse(BaseModel):
    session_id: str
    turn_id: str
    risk_level: RiskLevel
    risk_score: float
    fam_result: FAMResult
    echo_result: ECHOResult
    action_plan: ActionPlan
    response_steps: List[str]
    voice_text: str
    dispatch_status: str = "NONE"
    audit_id: str