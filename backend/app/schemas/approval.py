from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.app.models.approval import ApprovalStepStatus, ReimbursementStatus

class ApprovalActionRequest(BaseModel):
    action: str  # "APPROVE", "REJECT", "REQUEST_INFO"
    comments: Optional[str] = None

class ApprovalStepResponse(BaseModel):
    id: str
    request_id: str
    request_type: str
    approver_id: str
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    step_order: int
    status: ApprovalStepStatus
    comments: Optional[str]
    action_timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class ReimbursementResponse(BaseModel):
    id: str
    claim_id: str
    amount: float
    currency: str
    status: ReimbursementStatus
    transaction_ref: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
