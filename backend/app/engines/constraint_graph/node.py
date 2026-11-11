from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable
from backend.app.models.decision import ConstraintResult

@dataclass
class EvidenceRecord:
    result: ConstraintResult
    actual_condition: str
    expected_condition: str
    evidence_source: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConstraintNode:
    id: str
    name: str
    description: str
    category: str
    is_blocking: bool
    dependencies: List[str] = field(default_factory=list)
    evaluator: Optional[Callable[..., EvidenceRecord]] = None
    
    # Execution state
    status: Optional[ConstraintResult] = None
    evidence: Optional[EvidenceRecord] = None
    executed: bool = False
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_blocking": self.is_blocking,
            "dependencies": self.dependencies,
            "status": self.status.value if self.status else "NOT_EVALUATED",
            "executed": self.executed,
            "execution_time_ms": self.execution_time_ms,
            "evidence": {
                "result": self.evidence.result.value,
                "actual_condition": self.evidence.actual_condition,
                "expected_condition": self.evidence.expected_condition,
                "evidence_source": self.evidence.evidence_source,
                "reason": self.evidence.reason,
                "timestamp": self.evidence.timestamp,
                "details": self.evidence.details
            } if self.evidence else None
        }
