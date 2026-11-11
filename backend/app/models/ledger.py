import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ResourceType(str, enum.Enum):
    LEAVE_DAYS = "LEAVE_DAYS"
    BUDGET_AMOUNT = "BUDGET_AMOUNT"

class ReservationStatus(str, enum.Enum):
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"

class ResourceReservation(Base):
    __tablename__ = "resource_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(50), nullable=False, index=True)
    resource_type = Column(Enum(ResourceType), nullable=False)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
    cost_center_id = Column(String(50), ForeignKey("cost_centers.id"), nullable=True)
    leave_policy_id = Column(String(50), ForeignKey("leave_policies.id"), nullable=True)
    
    reserved_amount = Column(Numeric(12, 2), nullable=False)
    previous_available = Column(Numeric(12, 2), nullable=False)
    final_committed = Column(Numeric(12, 2), nullable=False, default=0.00)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.RESERVED, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee", foreign_keys=[employee_id])
    cost_center = relationship("CostCenter", foreign_keys=[cost_center_id])
    leave_policy = relationship("LeavePolicy", foreign_keys=[leave_policy_id])
