import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, date
from decimal import Decimal
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.expense import (
    ExpensePolicy, ExpenseClaim, ExpenseLine, ExpenseClaimStatus, ExpenseCategory
)
from backend.app.models.leave import DecisionState
from backend.app.models.employee import Employee, EmployeeRole, CostCenter
from backend.app.models.approval import ApprovalStep, ApprovalStepStatus
from backend.app.models.notification import Notification
from backend.app.schemas.expense import (
    ExpensePolicyResponse, ExpenseClaimCreate, ExpenseClaimResponse,
    ExpenseLineResponse, ExpenseDryRunRequest
)
from backend.app.api.deps import get_current_active_user
from backend.app.engines.algorithms.receipt_duplicate import calculate_sha256
from backend.app.engines.constraint_graph.builder import build_expense_constraint_graph
from backend.app.engines.decision.synthesizer import DecisionSynthesizer
from backend.app.engines.reservation.ledger import ResourceReservationLedger
from backend.app.engines.algorithms.authority_traversal import resolve_approval_chain
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/expenses", tags=["Expense Management"])

@router.get("/policies", response_model=List[ExpensePolicyResponse])
def get_expense_policies(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    policies = db.query(ExpensePolicy).all()
    results = []
    for p in policies:
        results.append(ExpensePolicyResponse(
            id=p.id,
            category=p.category,
            max_per_claim=float(p.max_per_claim),
            daily_limit=float(p.daily_limit),
            receipt_required_above=float(p.receipt_required_above),
            currency=p.currency,
            description=p.description
        ))
    return results

@router.post("/upload-receipt")
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Accepts uploaded receipt image/pdf, saves securely, and computes its SHA-256 hash
    for tamper-proof duplicate receipt detection.
    """
    contents = await file.read()
    receipt_hash = calculate_sha256(contents)

    filename = f"{receipt_hash[:16]}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    receipt_url = f"/uploads/{filename}"
    return {
        "filename": file.filename,
        "receipt_url": receipt_url,
        "receipt_hash": receipt_hash,
        "size_bytes": len(contents)
    }

@router.post("/dry-run")
def dry_run_expense(
    request: ExpenseDryRunRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Executes EFCG dry-run for an expense claim, checking policy ceilings,
    receipt verification, split-claim heuristic, budget headroom, and authority routing.
    """
    nodes = build_expense_constraint_graph(
        db=db,
        employee_id=current_user.id,
        cost_center_id=request.cost_center_id,
        category=request.category.value,
        merchant=request.merchant,
        claim_date=request.claim_date,
        total_amount=request.total_amount,
        receipt_url=request.receipt_url,
        receipt_hash=request.receipt_hash
    )

    evaluation = DecisionSynthesizer.execute_graph(
        nodes=nodes,
        db=db,
        request_id="",
        request_type="EXPENSE",
        persist_evaluations=False
    )

    return {
        "evaluation": evaluation
    }

@router.post("/claims", response_model=ExpenseClaimResponse)
def submit_expense_claim(
    request: ExpenseClaimCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    # Generate sequential Claim ID
    count = db.query(ExpenseClaim).count()
    claim_id = f"EXP-2026-{count + 1:06d}"

    # Stage 2 & 3: Build EFCG Graph and Evaluate Constraints
    nodes = build_expense_constraint_graph(
        db=db,
        employee_id=current_user.id,
        cost_center_id=request.cost_center_id,
        category=request.category.value,
        merchant=request.merchant,
        claim_date=request.claim_date,
        total_amount=request.total_amount,
        receipt_url=request.receipt_url,
        receipt_hash=request.receipt_hash,
        current_claim_id=claim_id
    )

    evaluation = DecisionSynthesizer.execute_graph(
        nodes=nodes,
        db=db,
        request_id=claim_id,
        request_type="EXPENSE",
        persist_evaluations=True
    )

    decision_state = DecisionState(evaluation["decision_state"])
    explanation = evaluation["explanation"]

    if decision_state == DecisionState.BLOCKED:
        initial_status = ExpenseClaimStatus.REJECTED
    elif decision_state == DecisionState.NEEDS_REVIEW:
        initial_status = ExpenseClaimStatus.SUBMITTED
    else:
        initial_status = ExpenseClaimStatus.PENDING_APPROVAL

    claim = ExpenseClaim(
        id=claim_id,
        employee_id=current_user.id,
        cost_center_id=request.cost_center_id,
        category=request.category,
        merchant=request.merchant,
        claim_date=request.claim_date,
        total_amount=request.total_amount,
        currency="USD",
        description=request.description,
        receipt_url=request.receipt_url,
        receipt_hash=request.receipt_hash,
        status=initial_status,
        decision_state=decision_state,
        decision_explanation=explanation
    )
    db.add(claim)
    db.flush()

    # Create line items
    lines = []
    if request.lines:
        for idx, line in enumerate(request.lines):
            line_id = f"EXPL-{claim_id}-{idx + 1:02d}"
            exp_line = ExpenseLine(
                id=line_id,
                claim_id=claim_id,
                line_number=idx + 1,
                category=line.category,
                description=line.description,
                amount=line.amount,
                receipt_hash=request.receipt_hash
            )
            db.add(exp_line)
            lines.append(exp_line)
    else:
        # Default single line item
        line_id = f"EXPL-{claim_id}-01"
        exp_line = ExpenseLine(
            id=line_id,
            claim_id=claim_id,
            line_number=1,
            category=request.category,
            description=request.description,
            amount=request.total_amount,
            receipt_hash=request.receipt_hash
        )
        db.add(exp_line)
        lines.append(exp_line)

    db.flush()

    # Stage 5: Resource Reservation & Authority Routing
    if decision_state in [DecisionState.ELIGIBLE, DecisionState.NEEDS_REVIEW]:
        # Atomic cost center budget reservation
        try:
            ResourceReservationLedger.reserve_expense_budget(
                db=db,
                request_id=claim_id,
                employee_id=current_user.id,
                cost_center_id=request.cost_center_id,
                amount=request.total_amount
            )
        except ValueError as e:
            # If budget reservation fails, mark as NEEDS_REVIEW
            claim.decision_state = DecisionState.NEEDS_REVIEW
            claim.decision_explanation += f" [Budget reservation deferred: {str(e)}]"

        # Generate approval chain
        approval_chain = resolve_approval_chain(
            db=db,
            employee_id=current_user.id,
            request_type="EXPENSE",
            amount_or_days=float(request.total_amount),
            category=request.category.value
        )

        for step in approval_chain:
            apr_id = f"APR-{claim_id}-{step['step_order']:02d}"
            apr_step = ApprovalStep(
                id=apr_id,
                request_id=claim_id,
                request_type="EXPENSE",
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
                title="Expense Approval Required",
                message=f"{current_user.first_name} {current_user.last_name} submitted claim {claim_id} for ${request.total_amount:,.2f} ({request.merchant}).",
                category="APPROVAL_PENDING",
                link_url=f"/requests/{claim_id}"
            ))

    # Stage 6: Tamper-Evident Audit Record
    AuditService.record_event(
        db=db,
        entity_type="EXPENSE_CLAIM",
        entity_id=claim_id,
        action="SUBMITTED",
        payload={
            "employee_id": current_user.id,
            "cost_center_id": request.cost_center_id,
            "merchant": request.merchant,
            "total_amount": float(request.total_amount),
            "receipt_hash": request.receipt_hash,
            "decision_state": decision_state.value,
            "status": initial_status.value
        },
        actor_id=current_user.id
    )

    db.commit()
    db.refresh(claim)

    cc = db.query(CostCenter).filter(CostCenter.id == claim.cost_center_id).first()
    return ExpenseClaimResponse(
        id=claim.id,
        employee_id=claim.employee_id,
        employee_name=f"{current_user.first_name} {current_user.last_name}",
        cost_center_id=claim.cost_center_id,
        cost_center_name=f"{cc.code} - {cc.name}" if cc else claim.cost_center_id,
        category=claim.category,
        merchant=claim.merchant,
        claim_date=claim.claim_date,
        total_amount=float(claim.total_amount),
        currency=claim.currency,
        description=claim.description,
        receipt_url=claim.receipt_url,
        receipt_hash=claim.receipt_hash,
        status=claim.status,
        decision_state=claim.decision_state,
        decision_explanation=claim.decision_explanation,
        lines=[
            ExpenseLineResponse(
                id=l.id,
                claim_id=l.claim_id,
                line_number=l.line_number,
                category=l.category,
                description=l.description,
                amount=float(l.amount),
                receipt_hash=l.receipt_hash
            )
            for l in lines
        ],
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )

@router.get("/claims", response_model=List[ExpenseClaimResponse])
def list_expense_claims(
    status: Optional[ExpenseClaimStatus] = None,
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(ExpenseClaim)

    if current_user.role == EmployeeRole.EMPLOYEE:
        query = query.filter(ExpenseClaim.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(ExpenseClaim.employee_id == employee_id)

    if status:
        query = query.filter(ExpenseClaim.status == status)

    claims = query.order_by(ExpenseClaim.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for c in claims:
        emp_name = f"{c.employee.first_name} {c.employee.last_name}" if c.employee else c.employee_id
        cc_name = f"{c.cost_center.code} - {c.cost_center.name}" if c.cost_center else c.cost_center_id
        results.append(ExpenseClaimResponse(
            id=c.id,
            employee_id=c.employee_id,
            employee_name=emp_name,
            cost_center_id=c.cost_center_id,
            cost_center_name=cc_name,
            category=c.category,
            merchant=c.merchant,
            claim_date=c.claim_date,
            total_amount=float(c.total_amount),
            currency=c.currency,
            description=c.description,
            receipt_url=c.receipt_url,
            receipt_hash=c.receipt_hash,
            status=c.status,
            decision_state=c.decision_state,
            decision_explanation=c.decision_explanation,
            lines=[
                ExpenseLineResponse(
                    id=l.id,
                    claim_id=l.claim_id,
                    line_number=l.line_number,
                    category=l.category,
                    description=l.description,
                    amount=float(l.amount),
                    receipt_hash=l.receipt_hash
                )
                for l in c.lines
            ],
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return results

@router.get("/claims/{id}", response_model=ExpenseClaimResponse)
def get_expense_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Expense claim not found")

    if current_user.role == EmployeeRole.EMPLOYEE and claim.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to claim")

    emp_name = f"{claim.employee.first_name} {claim.employee.last_name}" if claim.employee else claim.employee_id
    cc_name = f"{claim.cost_center.code} - {claim.cost_center.name}" if claim.cost_center else claim.cost_center_id

    return ExpenseClaimResponse(
        id=claim.id,
        employee_id=claim.employee_id,
        employee_name=emp_name,
        cost_center_id=claim.cost_center_id,
        cost_center_name=cc_name,
        category=claim.category,
        merchant=claim.merchant,
        claim_date=claim.claim_date,
        total_amount=float(claim.total_amount),
        currency=claim.currency,
        description=claim.description,
        receipt_url=claim.receipt_url,
        receipt_hash=claim.receipt_hash,
        status=claim.status,
        decision_state=claim.decision_state,
        decision_explanation=claim.decision_explanation,
        lines=[
            ExpenseLineResponse(
                id=l.id,
                claim_id=l.claim_id,
                line_number=l.line_number,
                category=l.category,
                description=l.description,
                amount=float(l.amount),
                receipt_hash=l.receipt_hash
            )
            for l in claim.lines
        ],
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )

@router.post("/claims/{id}/cancel")
def cancel_expense_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == id).with_for_update().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Expense claim not found")

    if current_user.role == EmployeeRole.EMPLOYEE and claim.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this claim")

    if claim.status in [ExpenseClaimStatus.CANCELLED, ExpenseClaimStatus.REJECTED, ExpenseClaimStatus.REIMBURSED]:
        raise HTTPException(status_code=400, detail=f"Claim is already {claim.status.value}")

    # Release budget reservation
    ResourceReservationLedger.release_expense_budget(db=db, request_id=id)

    # Cancel pending approval steps
    steps = db.query(ApprovalStep).filter(
        ApprovalStep.request_id == id,
        ApprovalStep.status == ApprovalStepStatus.PENDING
    ).all()
    for s in steps:
        s.status = ApprovalStepStatus.REJECTED
        s.comments = "Cancelled by user"
        s.action_timestamp = datetime.now(timezone.utc)

    claim.status = ExpenseClaimStatus.CANCELLED
    claim.updated_at = datetime.now(timezone.utc)

    AuditService.record_event(
        db=db,
        entity_type="EXPENSE_CLAIM",
        entity_id=id,
        action="CANCELLED",
        payload={"cancelled_by": current_user.id, "previous_status": claim.status.value},
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Expense claim {id} cancelled and reserved budget released successfully."}
