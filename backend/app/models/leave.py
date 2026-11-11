import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class LeaveRequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class DecisionState(str, enum.Enum):
    ELIGIBLE = "ELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"

class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id = Column(String(50), primary_key=True)  # e.g., "POL-ANNUAL"
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    days_per_year = Column(Float, nullable=False, default=20.0)
    max_consecutive_days = Column(Integer, default=15)
    carryover_allowed = Column(Integer, default=5)
    documentation_required_days = Column(Integer, default=3)  # requires doc if > N days
    employee_grade_min = Column(String(20), default="L1")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False, index=True)
    leave_policy_id = Column(String(50), ForeignKey("leave_policies.id"), nullable=False)
    year = Column(Integer, nullable=False, default=2026)
    allocated_days = Column(Float, nullable=False, default=20.0)
    used_days = Column(Float, nullable=False, default=0.0)
    reserved_days = Column(Float, nullable=False, default=0.0)  # Safe reservation ledger linkage

    employee = relationship("Employee", foreign_keys=[employee_id])
    policy = relationship("LeavePolicy", foreign_keys=[leave_policy_id])

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, index=True)
    country_code = Column(String(10), default="US", nullable=False)
    is_mandatory = Column(Integer, default=1)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(String(50), primary_key=True)  # e.g., "LVE-2026-000001"
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False, index=True)
    leave_policy_id = Column(String(50), ForeignKey("leave_policies.id"), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    total_days = Column(Float, nullable=False)
    business_days = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    document_url = Column(String(255), nullable=True)
    
    status = Column(Enum(LeaveRequestStatus), default=LeaveRequestStatus.SUBMITTED, nullable=False)
    decision_state = Column(Enum(DecisionState), default=DecisionState.NEEDS_REVIEW, nullable=False)
    decision_explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee", foreign_keys=[employee_id])
    policy = relationship("LeavePolicy", foreign_keys=[leave_policy_id])
