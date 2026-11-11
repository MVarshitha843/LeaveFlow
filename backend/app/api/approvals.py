from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from backend.app.core.database import get_db
from backend.app.models.approval import (
    ApprovalStep, ApprovalStepStatus, Reimbursement, ReimbursementStatus
)
from backend.app.models.leave import LeaveRequest, LeaveRequestStatus, DecisionState
from backend.app.models.expense import ExpenseClaim, ExpenseClaimStatus
from backend.app.models.employee import Employee, EmployeeRole
from backend.app.models.notification import Notification
from backend.app.schemas.approval import (
    ApprovalStepResponse, ApprovalActionRequest, ReimbursementResponse
)
from backend.app.api.deps import get_current_active_user, require_roles
from backend.app.engines.reservation.ledger import ResourceReservationLedger
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/approvals", tags=["Approvals & Workflows"])

@router.get("/pending")
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(ApprovalStep).filter(
        ApprovalStep.status == ApprovalStepStatus.PENDING
    )

    if current_user.role == EmployeeRole.ADMIN:
        # Admins can view all pending approvals
        pass
    elif current_user.role == EmployeeRole.FINANCE:
        # Finance sees steps assigned to them or unassigned finance steps
        query = query.filter(
            (ApprovalStep.approver_id == current_user.id) |
            (ApprovalStep.request_type == "EXPENSE")
        )
    else:
        # Managers see steps assigned to them
        query = query.filter(ApprovalStep.approver_id == current_user.id)

    pending_steps = query.order_by(ApprovalStep.created_at.asc()).all()

    results = []
    for step in pending_steps:
        applicant_name = "Unknown"
        applicant_id = ""
        summary_text = ""
        amount_or_days = 0.0

        if step.request_type == "LEAVE":
            lr = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).first()
            if lr and lr.employee:
                applicant_id = lr.employee.id
                applicant_name = f"{lr.employee.first_name} {lr.employee.last_name}"
                amount_or_days = lr.business_days
                summary_text = f"{lr.policy.name if lr.policy else 'Leave'}: {lr.start_date} to {lr.end_date} ({lr.business_days:.1f} days) - {lr.reason}"
        elif step.request_type == "EXPENSE":
            ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).first()
            if ec and ec.employee:
                applicant_id = ec.employee.id
                applicant_name = f"{ec.employee.first_name} {ec.employee.last_name}"
                amount_or_days = float(ec.total_amount)
                summary_text = f"{ec.category.value} at {ec.merchant}: ${amount_or_days:,.2f} - {ec.description}"

        # Segregation of duties: do not display self-approvals to applicant
        if applicant_id == current_user.id and current_user.role != EmployeeRole.ADMIN:
            continue

        approver_name = f"{step.approver.first_name} {step.approver.last_name}" if step.approver else step.approver_id

        results.append({
            "step_id": step.id,
            "request_id": step.request_id,
            "request_type": step.request_type,
            "step_order": step.step_order,
            "status": step.status.value,
            "applicant_id": applicant_id,
            "applicant_name": applicant_name,
            "approver_id": step.approver_id,
            "approver_name": approver_name,
            "amount_or_days": amount_or_days,
            "summary": summary_text,
            "created_at": step.created_at.isoformat()
        })
    return results

@router.get("/request/{request_id}", response_model=List[ApprovalStepResponse])
def get_request_approval_steps(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    steps = db.query(ApprovalStep).filter(
        ApprovalStep.request_id == request_id
    ).order_by(ApprovalStep.step_order.asc()).all()

    results = []
    for s in steps:
        app_name = f"{s.approver.first_name} {s.approver.last_name}" if s.approver else s.approver_id
        app_role = s.approver.role.value if s.approver else None
        results.append(ApprovalStepResponse(
            id=s.id,
            request_id=s.request_id,
            request_type=s.request_type,
            approver_id=s.approver_id,
            approver_name=app_name,
            approver_role=app_role,
            step_order=s.step_order,
            status=s.status,
            comments=s.comments,
            action_timestamp=s.action_timestamp,
            created_at=s.created_at
        ))
    return results

@router.post("/{step_id}/approve")
def approve_step(
    step_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    step = db.query(ApprovalStep).filter(ApprovalStep.id == step_id).with_for_update().first()
    if not step:
        raise HTTPException(status_code=404, detail="Approval step not found")

    if step.status != ApprovalStepStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Step is already {step.status.value}")

    # Identify applicant
    applicant_id = None
    if step.request_type == "LEAVE":
        lr = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).first()
        if lr: applicant_id = lr.employee_id
    elif step.request_type == "EXPENSE":
        ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).first()
        if ec: applicant_id = ec.employee_id

    # Anti-Self-Approval Enforcement
    if applicant_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CRITICAL SECURITY VIOLATION: Self-approval is strictly forbidden by platform policy."
        )

    # Verify authorization
    is_assigned = (step.approver_id == current_user.id)
    is_finance_authorized = (current_user.role == EmployeeRole.FINANCE and step.request_type == "EXPENSE")
    is_admin = (current_user.role == EmployeeRole.ADMIN)

    if not (is_assigned or is_finance_authorized or is_admin):
        raise HTTPException(status_code=403, detail="You are not authorized to approve this step")

    # Mark current step approved
    step.status = ApprovalStepStatus.APPROVED
    step.comments = body.comments or "Approved via portal"
    step.action_timestamp = datetime.now(timezone.utc)

    # Check if there are further pending steps
    other_pending = db.query(ApprovalStep).filter(
        ApprovalStep.request_id == step.request_id,
        ApprovalStep.step_order > step.step_order,
        ApprovalStep.status == ApprovalStepStatus.PENDING
    ).order_by(ApprovalStep.step_order.asc()).all()

    if other_pending:
        # Move to next step; notify next approver
        next_step = other_pending[0]
        db.add(Notification(
            recipient_id=next_step.approver_id,
            title="Approval Escalation Required",
            message=f"Request {step.request_id} has been approved by {current_user.first_name} {current_user.last_name} and is now pending your sign-off.",
            category="APPROVAL_PENDING",
            link_url=f"/requests/{step.request_id}"
        ))
        all_completed = False
    else:
        # All required steps are approved! Final commitment execution
        all_completed = True
        if step.request_type == "LEAVE":
            leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).with_for_update().first()
            if leave_req:
                leave_req.status = LeaveRequestStatus.APPROVED
                leave_req.updated_at = datetime.now(timezone.utc)
                # Commit reservation ledger!
                ResourceReservationLedger.commit_leave(db=db, request_id=step.request_id)
                # Notify applicant
                db.add(Notification(
                    recipient_id=leave_req.employee_id,
                    title="Leave Request Approved!",
                    message=f"Your leave request {leave_req.id} for {leave_req.business_days:.1f} days has been officially approved.",
                    category="REQUEST_APPROVED",
                    link_url=f"/requests/{leave_req.id}"
                ))

        elif step.request_type == "EXPENSE":
            claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).with_for_update().first()
            if claim:
                claim.status = ExpenseClaimStatus.APPROVED
                claim.updated_at = datetime.now(timezone.utc)
                # Commit budget reservation ledger!
                ResourceReservationLedger.commit_expense_budget(db=db, request_id=step.request_id)
                # Create pending Reimbursement record
                rmb_count = db.query(Reimbursement).count()
                reimbursement = Reimbursement(
                    id=f"RMB-2026-{rmb_count + 1:06d}",
                    claim_id=claim.id,
                    amount=claim.total_amount,
                    currency=claim.currency,
                    status=ReimbursementStatus.PENDING
                )
                db.add(reimbursement)
                # Notify applicant
                db.add(Notification(
                    recipient_id=claim.employee_id,
                    title="Expense Claim Approved!",
                    message=f"Your expense claim {claim.id} for ${claim.total_amount:,.2f} has been approved and queued for reimbursement.",
                    category="REQUEST_APPROVED",
                    link_url=f"/requests/{claim.id}"
                ))

    AuditService.record_event(
        db=db,
        entity_type=step.request_type,
        entity_id=step.request_id,
        action="STEP_APPROVED",
        payload={
            "step_id": step.id,
            "step_order": step.step_order,
            "approver_id": current_user.id,
            "comments": step.comments,
            "all_steps_completed": all_completed
        },
        actor_id=current_user.id
    )

    db.commit()
    return {
        "message": f"Step {step.id} approved successfully.",
        "final_approval": all_completed
    }

@router.post("/{step_id}/reject")
def reject_step(
    step_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    if not body.comments or body.comments.strip() == "":
        raise HTTPException(status_code=400, detail="Rejection reason comment is required by policy")

    step = db.query(ApprovalStep).filter(ApprovalStep.id == step_id).with_for_update().first()
    if not step:
        raise HTTPException(status_code=404, detail="Approval step not found")

    step.status = ApprovalStepStatus.REJECTED
    step.comments = body.comments
    step.action_timestamp = datetime.now(timezone.utc)

    # Reject request and release reservations
    if step.request_type == "LEAVE":
        lr = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).with_for_update().first()
        if lr:
            lr.status = LeaveRequestStatus.REJECTED
            lr.updated_at = datetime.now(timezone.utc)
            ResourceReservationLedger.release_leave(db=db, request_id=step.request_id)
            db.add(Notification(
                recipient_id=lr.employee_id,
                title="Leave Request Rejected",
                message=f"Your leave request {lr.id} was rejected by {current_user.first_name} {current_user.last_name}. Reason: {body.comments}",
                category="REQUEST_REJECTED",
                link_url=f"/requests/{lr.id}"
            ))

    elif step.request_type == "EXPENSE":
        ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).with_for_update().first()
        if ec:
            ec.status = ExpenseClaimStatus.REJECTED
            ec.updated_at = datetime.now(timezone.utc)
            ResourceReservationLedger.release_expense_budget(db=db, request_id=step.request_id)
            db.add(Notification(
                recipient_id=ec.employee_id,
                title="Expense Claim Rejected",
                message=f"Your expense claim {ec.id} was rejected by {current_user.first_name} {current_user.last_name}. Reason: {body.comments}",
                category="REQUEST_REJECTED",
                link_url=f"/requests/{ec.id}"
            ))

    AuditService.record_event(
        db=db,
        entity_type=step.request_type,
        entity_id=step.request_id,
        action="STEP_REJECTED",
        payload={
            "step_id": step.id,
            "approver_id": current_user.id,
            "reason": body.comments
        },
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Step {step.id} and request {step.request_id} rejected. Reserved balances released."}

@router.post("/{step_id}/request-information")
def request_information(
    step_id: str,
    body: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    if not body.comments or body.comments.strip() == "":
        raise HTTPException(status_code=400, detail="Explanation of required information is mandatory")

    step = db.query(ApprovalStep).filter(ApprovalStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Approval step not found")

    step.status = ApprovalStepStatus.INFO_REQUESTED
    step.comments = body.comments
    step.action_timestamp = datetime.now(timezone.utc)

    # Flag request as NEEDS_REVIEW
    applicant_id = None
    if step.request_type == "LEAVE":
        lr = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).first()
        if lr:
            lr.decision_state = DecisionState.NEEDS_REVIEW
            lr.status = LeaveRequestStatus.SUBMITTED
            applicant_id = lr.employee_id
    elif step.request_type == "EXPENSE":
        ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).first()
        if ec:
            ec.decision_state = DecisionState.NEEDS_REVIEW
            ec.status = ExpenseClaimStatus.SUBMITTED
            applicant_id = ec.employee_id

    if applicant_id:
        db.add(Notification(
            recipient_id=applicant_id,
            title="Additional Information Requested",
            message=f"{current_user.first_name} {current_user.last_name} requested more information on {step.request_id}: '{body.comments}'",
            category="INFO_REQUESTED",
            link_url=f"/requests/{step.request_id}"
        ))

    AuditService.record_event(
        db=db,
        entity_type=step.request_type,
        entity_id=step.request_id,
        action="INFO_REQUESTED",
        payload={"step_id": step.id, "requested_by": current_user.id, "query": body.comments},
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Information request logged and applicant notified for {step.request_id}."}

@router.post("/reimburse/{claim_id}", response_model=ReimbursementResponse)
def process_reimbursement(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.FINANCE, EmployeeRole.ADMIN]))
):
    """
    Finance authorization to disburse reimbursement for an APPROVED expense claim.
    """
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).with_for_update().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status != ExpenseClaimStatus.APPROVED:
        raise HTTPException(status_code=400, detail=f"Cannot reimburse claim with status '{claim.status.value}'. Must be 'APPROVED'.")

    rmb = db.query(Reimbursement).filter(Reimbursement.claim_id == claim_id).with_for_update().first()
    if not rmb:
        # Create reimbursement if not already generated
        rmb_count = db.query(Reimbursement).count()
        rmb = Reimbursement(
            id=f"RMB-2026-{rmb_count + 1:06d}",
            claim_id=claim.id,
            amount=claim.total_amount,
            currency=claim.currency,
            status=ReimbursementStatus.PENDING
        )
        db.add(rmb)
        db.flush()

    if rmb.status == ReimbursementStatus.PROCESSED:
        raise HTTPException(status_code=400, detail="Reimbursement has already been processed")

    # Generate transaction reference
    txn_ref = f"ACH-TXN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    rmb.status = ReimbursementStatus.PROCESSED
    rmb.transaction_ref = txn_ref
    rmb.processed_at = datetime.now(timezone.utc)

    claim.status = ExpenseClaimStatus.REIMBURSED
    claim.updated_at = datetime.now(timezone.utc)

    # Notify employee
    db.add(Notification(
        recipient_id=claim.employee_id,
        title="Reimbursement Disbursed!",
        message=f"Reimbursement of ${rmb.amount:,.2f} for claim {claim.id} has been processed (Ref: {txn_ref}).",
        category="REIMBURSEMENT_PROCESSED",
        link_url=f"/requests/{claim.id}"
    ))

    AuditService.record_event(
        db=db,
        entity_type="REIMBURSEMENT",
        entity_id=rmb.id,
        action="PROCESSED",
        payload={
            "claim_id": claim.id,
            "amount": float(rmb.amount),
            "transaction_ref": txn_ref,
            "processed_by": current_user.id
        },
        actor_id=current_user.id
    )

    db.commit()
    db.refresh(rmb)

    return ReimbursementResponse(
        id=rmb.id,
        claim_id=rmb.claim_id,
        amount=float(rmb.amount),
        currency=rmb.currency,
        status=rmb.status,
        transaction_ref=rmb.transaction_ref,
        processed_at=rmb.processed_at,
        created_at=rmb.created_at
    )
