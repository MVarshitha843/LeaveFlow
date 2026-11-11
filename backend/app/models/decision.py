import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from backend.app.core.database import Base

class ConstraintResult(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"

class ConstraintEvaluation(Base):
    __tablename__ = "constraint_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(50), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)  # "LEAVE" or "EXPENSE"
    constraint_name = Column(String(100), nullable=False)
    result = Column(Enum(ConstraintResult), nullable=False)
    actual_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    evidence_source = Column(String(100), nullable=True)
    evidence_summary = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(String(50), nullable=False)  # LEAVE_POLICY, EXPENSE_POLICY, APPROVAL_THRESHOLD
    version_number = Column(Integer, nullable=False, default=1)
    configuration_json = Column(Text, nullable=False)
    effective_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(50), nullable=False)  # Employee ID
    description = Column(Text, nullable=True)
