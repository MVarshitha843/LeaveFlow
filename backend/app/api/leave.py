from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, date
from backend.app.core.database import get_db
from backend.app.models.leave import (
    LeavePolicy, LeaveBalance, LeaveRequest, Holiday, LeaveRequestStatus, DecisionState
)
from backend.app.models.employee import Employee, EmployeeRole
from backend.app.models.approval import ApprovalStep, ApprovalStepStatus
from backend.app.models.notification import Notification
from backend.app.schemas.leave import (
    LeavePolicyResponse, LeaveBalanceResponse, LeaveRequestCreate, LeaveRequestResponse,
    LeaveDryRunRequest, HolidayResponse
)
from backend.app.api.deps import get_current_active_user
from backend.app.engines.algorithms.business_days import calculate_business_days
from backend.app.engines.constraint_graph.builder import build_leave_constraint_graph
from backend.app.engines.decision.synthesizer import DecisionSynthesizer
from backend.app.engines.reservation.ledger import ResourceReservationLedger
from backend.app.engines.algorithms.authority_traversal import resolve_approval_chain
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/leave", tags=["Leave Management"])

@router.get("/policies", response_model=List[LeavePolicyResponse])
def get_leave_policies(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    return db.query(LeavePolicy).all()

@router.get("/balances", response_model=List[LeaveBalanceResponse])
def get_leave_balances(
    employee_id: Optional[str] = None,
    year: int = 2026,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    target_emp_id = employee_id if (employee_id and current_user.role in [EmployeeRole.MANAGER, EmployeeRole.FINANCE, EmployeeRole.ADMIN]) else current_user.id
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == target_emp_id,
        LeaveBalance.year == year
    ).all()

    results = []
    for b in balances:
        avail = b.allocated_days - b.used_days - b.reserved_days
        results.append(LeaveBalanceResponse(
            id=b.id,
            employee_id=b.employee_id,
            leave_policy_id=b.leave_policy_id,
            policy_name=b.policy.name if b.policy else b.leave_policy_id,
            year=b.year,
            allocated_days=b.allocated_days,
            used_days=b.used_days,
            reserved_days=b.reserved_days,
            available_days=max(0.0, avail)
        ))
    return results

@router.get("/holidays", response_model=List[HolidayResponse])
def get_holidays(
    year: int = 2026,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    return db.query(Holiday).filter(Holiday.date >= date(year, 1, 1), Holiday.date <= date(year, 12, 31)).all()

@router.post("/dry-run")
def dry_run_leave(
    request: LeaveDryRunRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Simulates EFCG constraint evaluation for a proposed leave request without persisting.
    Provides instant validation feedback in the UI before form submission.
    """
    holidays = db.query(Holiday).all()
    holiday_dates = {h.date for h in holidays}
    b_days_calc = calculate_business_days(request.start_date, request.end_date, holiday_dates)

    nodes = build_leave_constraint_graph(
        db=db,
        employee_id=current_user.id,
        policy_id=request.policy_id,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        document_url=request.document_url
    )

    evaluation = DecisionSynthesizer.execute_graph(
        nodes=nodes,
        db=db,
        request_id="",
        request_type="LEAVE",
        persist_evaluations=False
    )

    return {
        "calculation": b_days_calc,
        "evaluation": evaluation
    }

@router.post("/requests", response_model=LeaveRequestResponse)
def submit_leave_request(
    request: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    # Calculate business days
    holidays = db.query(Holiday).all()
    holiday_dates = {h.date for h in holidays}
    b_days_info = calculate_business_days(request.start_date, request.end_date, holiday_dates)
    if not b_days_info["valid_range"]:
        raise HTTPException(status_code=400, detail=b_days_info["error"])

    # Generate sequential Request ID
    count = db.query(LeaveRequest).count()
    request_id = f"LVE-2026-{count + 1:06d}"
    calendar_days = (request.end_date - request.start_date).days + 1

    # Stage 2 & 3: Build EFCG Graph and Evaluate Constraints
    nodes = build_leave_constraint_graph(
        db=db,
        employee_id=current_user.id,
        policy_id=request.policy_id,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        document_url=request.document_url,
        current_request_id=request_id
    )

    evaluation = DecisionSynthesizer.execute_graph(
        nodes=nodes,
        db=db,
        request_id=request_id,
        request_type="LEAVE",
        persist_evaluations=True
    )

    decision_state = DecisionState(evaluation["decision_state"])
    explanation = evaluation["explanation"]

    # Determine initial request status
    if decision_state == DecisionState.BLOCKED:
        initial_status = LeaveRequestStatus.REJECTED
    elif decision_state == DecisionState.NEEDS_REVIEW:
        initial_status = LeaveRequestStatus.SUBMITTED
    else:
        initial_status = LeaveRequestStatus.PENDING_APPROVAL

    leave_req = LeaveRequest(
        id=request_id,
        employee_id=current_user.id,
        leave_policy_id=request.policy_id,
        start_date=request.start_date,
        end_date=request.end_date,
        total_days=float(calendar_days),
        business_days=float(b_days_info["business_days"]),
        reason=request.reason,
        document_url=request.document_url,
        status=initial_status,
        decision_state=decision_state,
        decision_explanation=explanation
    )
    db.add(leave_req)
    db.flush()

    # Stage 5: Resource Reservation & Authority Routing (Only when ELIGIBLE or NEEDS_REVIEW)
    if decision_state in [DecisionState.ELIGIBLE, DecisionState.NEEDS_REVIEW]:
        # Atomic balance reservation
        ResourceReservationLedger.reserve_leave(
            db=db,
            request_id=request_id,
            employee_id=current_user.id,
            leave_policy_id=request.policy_id,
            days=float(b_days_info["business_days"])
        )

        # Generate approval chain
        approval_chain = resolve_approval_chain(
            db=db,
            employee_id=current_user.id,
            request_type="LEAVE",
            amount_or_days=float(b_days_info["business_days"])
        )

        for step in approval_chain:
            apr_id = f"APR-{request_id}-{step['step_order']:02d}"
            apr_step = ApprovalStep(
                id=apr_id,
                request_id=request_id,
                request_type="LEAVE",
                approver_id=step["approver_id"],
                step_order=step["step_order"],
                status=ApprovalStepStatus.PENDING
            )
            db.add(apr_step)

        # Notify first approver
        if approval_chain:
            first_approver_id = approval_chain[0]["approver_id"]
            db.add(Notification(
                recipient_id=first_approver_id,
                title="Leave Approval Required",
                message=f"{current_user.first_name} {current_user.last_name} submitted {request_id} for {b_days_info['business_days']:.1f} business days.",
                category="APPROVAL_PENDING",
                link_url=f"/requests/{request_id}"
            ))

    # Stage 6: Proof-Carrying Tamper-Evident Audit Event
    AuditService.record_event(
        db=db,
        entity_type="LEAVE_REQUEST",
        entity_id=request_id,
        action="SUBMITTED",
        payload={
            "employee_id": current_user.id,
            "policy_id": request.policy_id,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "business_days": b_days_info["business_days"],
            "decision_state": decision_state.value,
            "status": initial_status.value
        },
        actor_id=current_user.id
    )

    db.commit()
    db.refresh(leave_req)

    return LeaveRequestResponse(
        id=leave_req.id,
        employee_id=leave_req.employee_id,
        employee_name=f"{current_user.first_name} {current_user.last_name}",
        leave_policy_id=leave_req.leave_policy_id,
        policy_name=leave_req.policy.name if leave_req.policy else leave_req.leave_policy_id,
        start_date=leave_req.start_date,
        end_date=leave_req.end_date,
        total_days=leave_req.total_days,
        business_days=leave_req.business_days,
        reason=leave_req.reason,
        document_url=leave_req.document_url,
        status=leave_req.status,
        decision_state=leave_req.decision_state,
        decision_explanation=leave_req.decision_explanation,
        created_at=leave_req.created_at,
        updated_at=leave_req.updated_at
    )

@router.get("/requests", response_model=List[LeaveRequestResponse])
def list_leave_requests(
    status: Optional[LeaveRequestStatus] = None,
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(LeaveRequest)

    # Scoping: Employees see their own; Managers see team/all; Finance/Admin see all
    if current_user.role == EmployeeRole.EMPLOYEE:
        query = query.filter(LeaveRequest.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)

    if status:
        query = query.filter(LeaveRequest.status == status)

    requests = query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for r in requests:
        emp_name = f"{r.employee.first_name} {r.employee.last_name}" if r.employee else r.employee_id
        pol_name = r.policy.name if r.policy else r.leave_policy_id
        results.append(LeaveRequestResponse(
            id=r.id,
            employee_id=r.employee_id,
            employee_name=emp_name,
            leave_policy_id=r.leave_policy_id,
            policy_name=pol_name,
            start_date=r.start_date,
            end_date=r.end_date,
            total_days=r.total_days,
            business_days=r.business_days,
            reason=r.reason,
            document_url=r.document_url,
            status=r.status,
            decision_state=r.decision_state,
            decision_explanation=r.decision_explanation,
            created_at=r.created_at,
            updated_at=r.updated_at
        ))
    return results

@router.get("/requests/{id}", response_model=LeaveRequestResponse)
def get_leave_request(
    id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if current_user.role == EmployeeRole.EMPLOYEE and req.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to request")

    emp_name = f"{req.employee.first_name} {req.employee.last_name}" if req.employee else req.employee_id
    pol_name = req.policy.name if req.policy else req.leave_policy_id

    return LeaveRequestResponse(
        id=req.id,
        employee_id=req.employee_id,
        employee_name=emp_name,
        leave_policy_id=req.leave_policy_id,
        policy_name=pol_name,
        start_date=req.start_date,
        end_date=req.end_date,
        total_days=req.total_days,
        business_days=req.business_days,
        reason=req.reason,
        document_url=req.document_url,
        status=req.status,
        decision_state=req.decision_state,
        decision_explanation=req.decision_explanation,
        created_at=req.created_at,
        updated_at=req.updated_at
    )

@router.post("/requests/{id}/cancel")
def cancel_leave_request(
    id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if current_user.role == EmployeeRole.EMPLOYEE and req.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this request")

    if req.status in [LeaveRequestStatus.CANCELLED, LeaveRequestStatus.REJECTED]:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    # Release reservation ledger hold
    ResourceReservationLedger.release_leave(db=db, request_id=id)

    # Cancel pending approval steps
    steps = db.query(ApprovalStep).filter(
        ApprovalStep.request_id == id,
        ApprovalStep.status == ApprovalStepStatus.PENDING
    ).all()
    for s in steps:
        s.status = ApprovalStepStatus.REJECTED
        s.comments = "Cancelled by user"
        s.action_timestamp = datetime.now(timezone.utc)

    req.status = LeaveRequestStatus.CANCELLED
    req.updated_at = datetime.now(timezone.utc)

    AuditService.record_event(
        db=db,
        entity_type="LEAVE_REQUEST",
        entity_id=id,
        action="CANCELLED",
        payload={"cancelled_by": current_user.id, "previous_status": req.status.value},
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Leave request {id} cancelled and reserved balance released successfully."}
