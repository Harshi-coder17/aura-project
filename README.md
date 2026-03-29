# AURA — Autonomous Understanding & Response Agent

> **The AI that doesn't just know what happened — it knows how panicked you are.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react" />
  <img src="https://img.shields.io/badge/XGBoost-ML-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/License-BUSL--1.1-red?style=flat-square" />
</p>

---

## What is AURA?

AURA is an AI-powered real-time emergency response system that goes beyond traditional first-aid chatbots. Most emergency AI systems know *what* happened — AURA also understands *how the person is feeling* and adapts everything accordingly: the language, the number of steps, the voice output, and the transport decision.

It does this through two core AI engines running in parallel:

- **FAM (First Aid Machine)** — Extracts structured medical context from text, voice, and images. Identifies the injury, severity, affected body part, and matched first-aid protocol.
- **ECHO (Emotional & Cognitive Health Observer)** — A 5-stage behavioral risk pipeline that scores user panic level using a 19-dimensional feature vector. When a user is panicking, ECHO detects it and forces the system to simplify: 3 steps instead of 8, larger text, auto voice playback.

The combination means AURA gives the *right* response *in the right format* for the person's actual cognitive state — not a one-size-fits-all answer.

---

## The Problem AURA Solves

| Failure Type | What Happens Today | What AURA Does |
|---|---|---|
| **Situational Blindness** | AI processes inputs without understanding severity or context | FAM extracts typed, confidence-scored medical entities with matched protocols |
| **Human State Ignorance** | Panic, confusion, and cognitive overload are invisible to AI | ECHO detects psychological state via 19 behavioral signals and simplifies output proportionally |
| **Audit & Trust Deficit** | No explainability, no decision trail, no accountability | Every decision, score, and action is logged immutably with full rationale |

---

## Key Features

- 🧠 **8-Stage AI Pipeline** — Input → FAM → ECHO → Context → Decision → Response → Action → Audit. Each stage has a single typed responsibility.
- 🚨 **ECHO Adaptive UI** — When risk is HIGH or CRITICAL, the entire interface changes: steps reduce to 3, font size increases, voice auto-plays, and the ambulance hold-to-call button appears.
- 👤 **Personal vs Stranger Mode** — Personal mode uses your medical profile (conditions, allergies, medications) to personalise protocols and escalate severity when your condition is at risk. Stranger mode uses conservative safe defaults.
- 🏥 **Live Hospital Map** — Nearest hospitals ranked by distance with ETA. One tap to call.
- 🚑 **Transport Decision Engine** — Automatically recommends Ambulance, Priority Cab, or Self-care based on injury severity and behavioral risk. Hold-to-call ambulance (3 seconds) for safety against accidental triggers.
- 🔊 **Voice Instructions** — Auto-plays for HIGH/CRITICAL risk. Available on-click for all cases.
- 🛡️ **Medical Rule Engine** — Every AI-generated instruction is validated against 30+ hard safety rules before reaching the user. "Apply butter to a burn" is blocked. "Cool with running water" passes.
- 📋 **Full Audit Trail** — Every session is logged: FAM output, ECHO scores, decision rationale, transport taken, blocked instructions. Queryable via `/api/v1/audit`.
- 🔁 **OpenAI Fallback** — When OpenAI quota is exhausted, FAM falls back to a lexicon-based extractor driven entirely by `protocols.json`. No crash, no empty response.

---

## System Architecture

```
USER INPUT (Voice / Text / Image)
         │
         ▼
┌─────────────────────────┐
│   INPUT PROCESSING       │  ← Whisper STT, GPT-4V, LangDetect
└────────────┬────────────┘
             │ Structured Payload
             ▼
┌─────────────────────────┐
│   FAM — UNDERSTANDING    │  ← spaCy NER + Protocol Library + Image Fusion
└────────────┬────────────┘
             │ Situational Context
             ▼
┌─────────────────────────┐
│   ECHO — BEHAVIORAL RISK │  ← XGBoost + 19-Feature Vector + Rules
└────────────┬────────────┘
             │ Risk Score + Calibration Mode
             ▼
┌─────────────────────────┐
│   CONTEXT AWARENESS      │  ← Weather API, Disease API, Google Maps
└────────────┬────────────┘
             │ Environmental Context
             ▼
┌─────────────────────────┐
│   DECISION ENGINE        │  ← Composite scoring + Rule-based orchestration
└──────┬──────────┬───────┘
       │          │
       ▼          ▼
┌──────────┐  ┌──────────────┐
│ RESPONSE │  │ ACTION LAYER │  ← Dispatch, Notify, Map
│  ENGINE  │  │              │
└────┬─────┘  └──────┬───────┘
     └────────┬───────┘
              ▼
┌─────────────────────────┐
│   AUDIT & LEARNING       │  ← PostgreSQL + Feedback loop
└─────────────────────────┘
              │
              ▼
    USER INTERFACE OUTPUT
  (Voice + Text + Map + Actions)
```

---

## ECHO: The Core Innovation

ECHO is what separates AURA from every existing emergency AI. It extracts a **19-dimensional behavioral feature vector** from each user message:

| # | Feature | What It Measures |
|---|---|---|
| 1–5 | Intent distribution | Harm, dependency, inquiry, panic, other |
| 6 | Valence | Emotional positivity vs negativity [-1, 1] |
| 7 | Arousal | Activation / urgency level — HIGH = panic |
| 8 | Dominance | Sense of control vs helplessness |
| 9 | Alpha auth | Authority transfer — user surrendering decisions |
| 10 | Alpha attachment | Over-reliance signals |
| 11 | Alpha hedge | Reduction in hedging language = increasing panic |
| 12 | Flag jailbreak | Attempts to override safety constraints |
| 13 | Flag critical | Crisis phrases (suicidal ideation, extreme distress) |
| 14 | Harm keyword density | High-risk words as proportion of message |
| 15 | Trend distress | Rate of change of distress across session |
| 16 | Reassurance count | Times user asked for reassurance this session |
| 17 | Topic entropy | High entropy = scattered/panicking mind |
| 18 | Message length | Very short = panic; very long = rumination |
| 19 | Question ratio | High = uncertainty and helplessness |

**Composite Risk Formula:**
```
final_risk = (0.50 × ml_score) + (0.30 × rule_score) + (0.20 × context_score)
```

| Risk Level | Score Range | System Response |
|---|---|---|
| LOW | 0.00 – 0.25 | PASSTHROUGH — full protocol, normal UI |
| MEDIUM | 0.25 – 0.50 | HEDGE_INJECT — add safety caveats |
| HIGH | 0.50 – 0.75 | FULL_REWRITE — 3 steps, voice forced, large text |
| CRITICAL | 0.75 – 1.00 | CRISIS_REDIRECT — emergency services only |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind CSS | Component reusability, real-time UI, mobile-first |
| Backend | FastAPI + Python 3.11 | Async-native for concurrent LLM + API calls |
| Database | SQLite (dev) / PostgreSQL (prod) | ACID for audit logs, JSONB for medical schemas |
| ML | XGBoost + scikit-learn | Fast inference (<5ms), SHAP explainability |
| GenAI | OpenAI GPT-4o | Best instruction following, structured output |
| STT | Web Speech API | Browser-native, no API cost for MVP |
| TTS | Web Speech Synthesis API | Browser-native voice output |
| Maps | Google Maps API (fallback: mock) | Hospital lookup, distance ranking |
| Hosting | Render (backend) + Vercel (frontend) | Free tier, auto-deploy on push |

---

## Project Structure

```
aura-project/
├── backend/
│   ├── main.py                    # FastAPI app — 8-stage pipeline
│   ├── aura/
│   │   ├── agents/
│   │   │   ├── input_processor.py # Stage 1 — multimodal input
│   │   │   ├── fam_agent.py       # Stage 2 — medical entity extraction
│   │   │   ├── echo_engine.py     # Stage 3 — behavioral risk scoring
│   │   │   ├── context_agent.py   # Stage 4 — environment enrichment
│   │   │   ├── decision_engine.py # Stage 5 — action plan synthesis
│   │   │   ├── response_engine.py # Stage 6 — verified response generation
│   │   │   ├── action_layer.py    # Stage 7 — dispatch execution
│   │   │   └── audit_layer.py     # Stage 8 — immutable decision log
│   │   ├── models.py              # Shared Pydantic models
│   │   ├── config.py              # Settings and environment
│   │   └── database.py            # SQLAlchemy async DB layer
│   └── data/
│       ├── protocols/
│       │   └── protocols.json     # 10+ validated first-aid protocol trees
│       └── lexicons/
│           ├── crisis_phrases.txt
│           ├── panic_phrases.txt
│           ├── harm_keywords.txt
│           └── authority_phrases.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── HomeScreen.jsx
│       │   ├── InputScreen.jsx
│       │   ├── GuidanceScreen.jsx # ECHO-adaptive UI
│       │   ├── MapScreen.jsx
│       │   ├── ModeToggle.jsx
│       │   └── Toast.jsx
│       └── hooks/
│           └── useAura.js         # API layer with geolocation
├── LICENSE
├── CONTRIBUTORS.md
└── render.yaml
```

---


**Example Request:**
```json
POST /api/v1/process
{
  "session_id": "a3f8b2c1-...",
  "mode": "personal",
  "user_id": "user_demo",
  "text": "I burned my hand badly on the stove",
  "turn_number": 1
}
```

**Example Response:**
```json
{
  "risk_level": "CRITICAL",
  "risk_score": 0.90,
  "fam_result": {
    "injury": "Severe Thermal Burn",
    "severity": "CRITICAL",
    "protocol_code": "BURN_SEVERE_001",
    "personal_flags": ["diabetic", "hypertension"]
  },
  "action_plan": { "transport": "AMBULANCE" },
  "response_steps": [
    "Hold the burned area under cool running water for 10-20 minutes.",
    "Do NOT apply ice, butter, toothpaste, or any cream.",
    "Remove jewelry near the burn before swelling starts."
  ],
  "voice_text": "Step 1: Hold burned area under cool water. Step 2: Do not apply ice or butter. Step 3: Remove jewelry now.",
  "audit_id": "A3F8B2C1"
}
```

---

## The Team

Built by **Team LowkeyCoders** for [Hackathon Name] 2026.

| Name | Role | GitHub |
|---|---|---|
| Harshita | Frontend & Integration | [@Harshi-coder17](https://github.com/Harshi-coder17) |
| Adhiraj Singh Saini | AI/ML Pipeline | [@AdhirajCoder16](https://github.com/AdhirajCoder16) |
| Iksha | Frontend & UX | [@Iksha-Goomer](https://github.com/Iksha-Goomer) |
| Armaan Malhotra | Backend & API | [@armaan-1207](https://github.com/armaan-1207) |

All members are students at **TIET, Patiala, Punjab, India.**

---

## License

Protected under the **Business Source License 1.1**.
Hackathon evaluators may view and run this project for assessment purposes only.
No copying, forking, or redistribution without written permission from all four authors.

See [LICENSE](./LICENSE) for full terms.

---

> *"No one faces an emergency alone — and no workflow fails silently."*
>
> — Team LowkeyCoders
