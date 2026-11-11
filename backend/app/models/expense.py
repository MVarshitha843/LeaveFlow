import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.leave import DecisionState

class ExpenseClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REIMBURSED = "REIMBURSED"

class ExpenseCategory(str, enum.Enum):
    TRAVEL = "TRAVEL"
    MEALS = "MEALS"
    LODGING = "LODGING"
    EQUIPMENT = "EQUIPMENT"
    SOFTWARE = "SOFTWARE"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    OTHER = "OTHER"

class ExpensePolicy(Base):
    __tablename__ = "expense_policies"

    id = Column(String(50), primary_key=True)  # e.g., "POL-EXP-MEALS"
    category = Column(Enum(ExpenseCategory), nullable=False, unique=True)
    max_per_claim = Column(Numeric(10, 2), nullable=False, default=500.00)
    daily_limit = Column(Numeric(10, 2), nullable=False, default=100.00)
    receipt_required_above = Column(Numeric(10, 2), nullable=False, default=25.00)
    currency = Column(String(10), default="USD", nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id = Column(String(50), primary_key=True)  # e.g., "EXP-2026-000001"
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False, index=True)
    cost_center_id = Column(String(50), ForeignKey("cost_centers.id"), nullable=False, index=True)
    category = Column(Enum(ExpenseCategory), nullable=False)
    merchant = Column(String(150), nullable=False)
    claim_date = Column(Date, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    description = Column(Text, nullable=False)
    receipt_url = Column(String(255), nullable=True)
    receipt_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash of receipt

    status = Column(Enum(ExpenseClaimStatus), default=ExpenseClaimStatus.SUBMITTED, nullable=False)
    decision_state = Column(Enum(DecisionState), default=DecisionState.NEEDS_REVIEW, nullable=False)
    decision_explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee", foreign_keys=[employee_id])
    cost_center = relationship("CostCenter", foreign_keys=[cost_center_id])
    lines = relationship("ExpenseLine", back_populates="claim", cascade="all, delete-orphan")

class ExpenseLine(Base):
    __tablename__ = "expense_lines"

    id = Column(String(60), primary_key=True)  # e.g., "EXPL-EXP-2026-000001-01"
    claim_id = Column(String(50), ForeignKey("expense_claims.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_hash = Column(String(64), nullable=True)

    claim = relationship("ExpenseClaim", back_populates="lines")
