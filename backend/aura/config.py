import os
from functools import lru_cache


class Settings:
    # ── AI Keys ──────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # ── Maps ─────────────────────────────────────────────────
    GOOGLE_MAPS_KEY: str = os.getenv("GOOGLE_MAPS_KEY", "")

    # ── Database ─────────────────────────────────────────────
    # Supabase connection string (Member 4 will provide this)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./aura.db"  # fallback for local dev
    )

    # ── ECHO Risk Thresholds ──────────────────────────────────
    RISK_LOW: float = float(os.getenv("RISK_LOW", "0.25"))
    RISK_MEDIUM: float = float(os.getenv("RISK_MEDIUM", "0.50"))
    RISK_HIGH: float = float(os.getenv("RISK_HIGH", "0.75"))

    # ── Session ───────────────────────────────────────────────
    SESSION_TTL_SEC: int = int(os.getenv("SESSION_TTL_SEC", "14400"))

    # ── App ───────────────────────────────────────────────────
    APP_NAME: str = "AURA"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

