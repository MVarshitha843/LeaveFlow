from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from backend.app.models.leave import LeaveRequestStatus, DecisionState

class LeaveDryRunRequest(BaseModel):
    policy_id: str
    start_date: date
    end_date: date
    reason: str
    document_url: Optional[str] = None

class LeaveRequestCreate(BaseModel):
    policy_id: str
    start_date: date
    end_date: date
    reason: str
    document_url: Optional[str] = None

class LeavePolicyResponse(BaseModel):
    id: str
    code: str
    name: str
    days_per_year: float
    max_consecutive_days: int
    carryover_allowed: int
    documentation_required_days: int
    employee_grade_min: str
    description: Optional[str]

    class Config:
        from_attributes = True

class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: str
    leave_policy_id: str
    policy_name: Optional[str] = None
    year: int
    allocated_days: float
    used_days: float
    reserved_days: float
    available_days: float

    class Config:
        from_attributes = True

class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    leave_policy_id: str
    policy_name: Optional[str] = None
    start_date: date
    end_date: date
    total_days: float
    business_days: float
    reason: str
    document_url: Optional[str]
    status: LeaveRequestStatus
    decision_state: DecisionState
    decision_explanation: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HolidayResponse(BaseModel):
    id: int
    name: str
    date: date
    country_code: str
    is_mandatory: int

    class Config:
        from_attributes = True
