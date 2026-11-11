from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AuditEventResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    actor_id: Optional[str]
    previous_hash: str
    current_hash: str
    payload_json: str
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_events: int
    head_hash: Optional[str] = None
    corrupted_event_id: Optional[int] = None
    error_type: Optional[str] = None
    message: str
