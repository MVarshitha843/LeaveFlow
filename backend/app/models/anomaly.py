import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AnomalySeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AnomalyStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    RESOLVED = "RESOLVED"

class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_type = Column(String(100), nullable=False, index=True)
    request_id = Column(String(50), nullable=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=True, index=True)
    severity = Column(Enum(AnomalySeverity), default=AnomalySeverity.MEDIUM, nullable=False)
    detection_method = Column(String(100), nullable=False)
    evidence_json = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=True)
    status = Column(Enum(AnomalyStatus), default=AnomalyStatus.OPEN, nullable=False)
    resolved_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee", foreign_keys=[employee_id])
