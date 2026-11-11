from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_db
from backend.app.models.decision import ConstraintEvaluation
from backend.app.models.leave import LeaveRequest
from backend.app.models.expense import ExpenseClaim
from backend.app.models.employee import Employee
from backend.app.schemas.decision import (
    ConstraintEvaluationResponse, EFCGGraphResponse, GraphNodeResponse, GraphEdgeResponse
)
from backend.app.api.deps import get_current_active_user
from backend.app.engines.constraint_graph.builder import (
    build_leave_constraint_graph, build_expense_constraint_graph
)
from backend.app.engines.decision.synthesizer import DecisionSynthesizer

router = APIRouter(prefix="/decision", tags=["EFCG Decision Engine"])

@router.get("/{request_id}")
def get_decision_details(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Returns stored constraint evaluations and explainable natural language rationale
    for a given request.
    """
    evaluations = db.query(ConstraintEvaluation).filter(
        ConstraintEvaluation.request_id == request_id
    ).order_by(ConstraintEvaluation.executed_at.asc()).all()

    request_obj = None
    req_type = "LEAVE" if request_id.startswith("LVE") else "EXPENSE"

    if req_type == "LEAVE":
        request_obj = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    else:
        request_obj = db.query(ExpenseClaim).filter(ExpenseClaim.id == request_id).first()

    if not request_obj:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

    return {
        "request_id": request_id,
        "request_type": req_type,
        "decision_state": request_obj.decision_state.value,
        "status": request_obj.status.value,
        "decision_explanation": request_obj.decision_explanation,
        "evaluations": [
            ConstraintEvaluationResponse(
                id=e.id,
                request_id=e.request_id,
                request_type=e.request_type,
                constraint_name=e.constraint_name,
                result=e.result,
                actual_value=e.actual_value,
                expected_value=e.expected_value,
                evidence_source=e.evidence_source,
                evidence_summary=e.evidence_summary,
                executed_at=e.executed_at
            )
            for e in evaluations
        ]
    }

@router.get("/{request_id}/graph", response_model=EFCGGraphResponse)
def get_decision_graph(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Reconstructs the full live DAG constraint graph for the request,
    including node statuses (PASS/FAIL/REVIEW), evidence details, dependency edges,
    and topological execution order for interactive frontend visualization.
    """
    if request_id.startswith("LVE"):
        lr = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not lr:
            raise HTTPException(status_code=404, detail="Leave request not found")
        nodes = build_leave_constraint_graph(
            db=db,
            employee_id=lr.employee_id,
            policy_id=lr.leave_policy_id,
            start_date=lr.start_date,
            end_date=lr.end_date,
            reason=lr.reason,
            document_url=lr.document_url,
            current_request_id=lr.id
        )
        res = DecisionSynthesizer.execute_graph(
            nodes=nodes,
            db=db,
            request_id=request_id,
            request_type="LEAVE",
            persist_evaluations=False
        )
        req_type = "LEAVE"
    elif request_id.startswith("EXP"):
        ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == request_id).first()
        if not ec:
            raise HTTPException(status_code=404, detail="Expense claim not found")
        nodes = build_expense_constraint_graph(
            db=db,
            employee_id=ec.employee_id,
            cost_center_id=ec.cost_center_id,
            category=ec.category.value,
            merchant=ec.merchant,
            claim_date=ec.claim_date,
            total_amount=ec.total_amount,
            receipt_url=ec.receipt_url,
            receipt_hash=ec.receipt_hash,
            current_claim_id=ec.id
        )
        res = DecisionSynthesizer.execute_graph(
            nodes=nodes,
            db=db,
            request_id=request_id,
            request_type="EXPENSE",
            persist_evaluations=False
        )
        req_type = "EXPENSE"
    else:
        raise HTTPException(status_code=400, detail="Unknown request identifier pattern")

    return EFCGGraphResponse(
        request_id=request_id,
        request_type=req_type,
        decision_state=res["decision_state"],
        explanation=res["explanation"],
        summary=res["summary"],
        nodes=[GraphNodeResponse(**n) for n in res["nodes"]],
        edges=[GraphEdgeResponse(**e) for e in res["edges"]],
        execution_order=res["execution_order"]
    )
