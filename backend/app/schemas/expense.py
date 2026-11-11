from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from backend.app.models.expense import ExpenseClaimStatus, ExpenseCategory
from backend.app.models.leave import DecisionState

class ExpenseLineCreate(BaseModel):
    category: ExpenseCategory
    description: str
    amount: Decimal

class ExpenseLineResponse(BaseModel):
    id: str
    claim_id: str
    line_number: int
    category: ExpenseCategory
    description: str
    amount: float
    receipt_hash: Optional[str]

    class Config:
        from_attributes = True

class ExpenseDryRunRequest(BaseModel):
    cost_center_id: str
    category: ExpenseCategory
    merchant: str
    claim_date: date
    total_amount: Decimal
    description: str
    receipt_url: Optional[str] = None
    receipt_hash: Optional[str] = None
    lines: Optional[List[ExpenseLineCreate]] = None

class ExpenseClaimCreate(BaseModel):
    cost_center_id: str
    category: ExpenseCategory
    merchant: str
    claim_date: date
    total_amount: Decimal
    description: str
    receipt_url: Optional[str] = None
    receipt_hash: Optional[str] = None
    lines: Optional[List[ExpenseLineCreate]] = None

class ExpensePolicyResponse(BaseModel):
    id: str
    category: ExpenseCategory
    max_per_claim: float
    daily_limit: float
    receipt_required_above: float
    currency: str
    description: Optional[str]

    class Config:
        from_attributes = True

class ExpenseClaimResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    cost_center_id: str
    cost_center_name: Optional[str] = None
    category: ExpenseCategory
    merchant: str
    claim_date: date
    total_amount: float
    currency: str
    description: str
    receipt_url: Optional[str]
    receipt_hash: Optional[str]
    status: ExpenseClaimStatus
    decision_state: DecisionState
    decision_explanation: Optional[str]
    lines: List[ExpenseLineResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
