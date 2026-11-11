from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from backend.app.models.anomaly import AnomalySeverity, AnomalyStatus

class AnomalyReviewRequest(BaseModel):
    status: AnomalyStatus
    notes: Optional[str] = None

class AnomalyAlertResponse(BaseModel):
    id: int
    anomaly_type: str
    request_id: Optional[str]
    employee_id: Optional[str]
    employee_name: Optional[str] = None
    severity: AnomalySeverity
    detection_method: str
    evidence_json: str
    explanation: str
    suggested_action: Optional[str]
    status: AnomalyStatus
    resolved_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
