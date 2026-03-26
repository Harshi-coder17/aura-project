from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from datetime import datetime, timezone
from aura.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"statement_cache_size": 0}
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"
    session_id    = Column(String(36), primary_key=True)
    user_id       = Column(String(36), nullable=True)
    mode          = Column(String(20), default="stranger")
    started_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at      = Column(DateTime, nullable=True)
    final_severity= Column(String(20), nullable=True)
    outcome       = Column(String(50), nullable=True)


class EventRecord(Base):
    __tablename__ = "events"
    event_id      = Column(String(36), primary_key=True)
    session_id    = Column(String(36), nullable=False)
    turn_number   = Column(Integer, default=1)
    timestamp     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    input_text    = Column(Text, nullable=True)
    fam_output    = Column(JSON, nullable=True)
    echo_output   = Column(JSON, nullable=True)
    decision      = Column(JSON, nullable=True)
    response_steps= Column(JSON, nullable=True)
    was_modified  = Column(Boolean, default=False)
    blocked_steps = Column(Integer, default=0)
    dispatch_status= Column(String(30), default="NONE")
    audit_id      = Column(String(8), nullable=True)


class UserProfileRecord(Base):
    __tablename__ = "user_profiles"
    user_id       = Column(String(36), primary_key=True)
    name          = Column(String(100), default="User")
    age           = Column(Integer, nullable=True)
    blood_group   = Column(String(5), nullable=True)
    conditions    = Column(JSON, default=list)
    allergies     = Column(JSON, default=list)
    medications   = Column(JSON, default=list)
    emergency_contacts = Column(JSON, default=list)


async def init_db():
    """Create all tables. Call on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency injection for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
