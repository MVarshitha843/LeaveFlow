from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.models.decision import ConstraintResult

class ConstraintEvaluationResponse(BaseModel):
    id: int
    request_id: str
    request_type: str
    constraint_name: str
    result: ConstraintResult
    actual_value: Optional[str]
    expected_value: Optional[str]
    evidence_source: Optional[str]
    evidence_summary: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True

class GraphNodeResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    is_blocking: bool
    dependencies: List[str]
    status: str
    executed: bool
    execution_time_ms: float
    evidence: Optional[Dict[str, Any]]

class GraphEdgeResponse(BaseModel):
    source: str
    target: str

class EFCGGraphResponse(BaseModel):
    request_id: str
    request_type: str
    decision_state: str
    explanation: str
    summary: Dict[str, int]
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    execution_order: List[str]
