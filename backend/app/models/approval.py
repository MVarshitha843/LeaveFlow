import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.employee import EmployeeRole

class ApprovalStepStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INFO_REQUESTED = "INFO_REQUESTED"

class ReimbursementStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"

class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_type = Column(String(20), nullable=False)  # "LEAVE" or "EXPENSE"
    min_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    max_amount = Column(Numeric(10, 2), default=999999.00, nullable=False)
    required_role = Column(Enum(EmployeeRole), nullable=False)
    step_order = Column(Integer, nullable=False, default=1)
    description = Column(String(255), nullable=True)

class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(String(80), primary_key=True)  # e.g., "APR-EXP-2026-000001-01"
    request_id = Column(String(50), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)  # "LEAVE" or "EXPENSE"
    approver_id = Column(String(50), ForeignKey("employees.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False, default=1)
    status = Column(Enum(ApprovalStepStatus), default=ApprovalStepStatus.PENDING, nullable=False)
    comments = Column(Text, nullable=True)
    action_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    approver = relationship("Employee", foreign_keys=[approver_id])

class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(String(50), primary_key=True)  # e.g., "RMB-2026-000001"
    claim_id = Column(String(50), ForeignKey("expense_claims.id"), nullable=False, unique=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(Enum(ReimbursementStatus), default=ReimbursementStatus.PENDING, nullable=False)
    transaction_ref = Column(String(100), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    claim = relationship("ExpenseClaim", foreign_keys=[claim_id])
