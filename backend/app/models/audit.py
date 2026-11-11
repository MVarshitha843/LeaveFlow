from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    actor_id = Column(String(50), nullable=True)  # Employee ID or "SYSTEM"
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, unique=True, index=True)
    payload_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
