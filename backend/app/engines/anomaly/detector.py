import json
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.anomaly import AnomalyAlert, AnomalySeverity, AnomalyStatus
from backend.app.models.employee import Employee, CostCenter
from backend.app.models.leave import LeaveRequest, LeaveBalance, LeaveRequestStatus
from backend.app.models.expense import ExpenseClaim, ExpensePolicy, ExpenseClaimStatus
from backend.app.models.approval import ApprovalStep, Reimbursement

class AnomalyDetector:
    """
    Enterprise Anomaly Detection Engine covering 12 distinct anomaly classifications.
    Provides automated pattern scanning, severity grading, and evidence capture.
    """

    @classmethod
    def record_alert(
        cls,
        db: Session,
        anomaly_type: str,
        severity: AnomalySeverity,
        detection_method: str,
        explanation: str,
        suggested_action: str,
        evidence: Dict[str, Any],
        request_id: Optional[str] = None,
        employee_id: Optional[str] = None
    ) -> AnomalyAlert:
        # Check if identical open alert already exists
        existing = db.query(AnomalyAlert).filter(
            AnomalyAlert.anomaly_type == anomaly_type,
            AnomalyAlert.request_id == request_id,
            AnomalyAlert.status.in_([AnomalyStatus.OPEN, AnomalyStatus.UNDER_REVIEW])
        ).first()

        if existing:
            return existing

        alert = AnomalyAlert(
            anomaly_type=anomaly_type,
            request_id=request_id,
            employee_id=employee_id,
            severity=severity,
            detection_method=detection_method,
            evidence_json=json.dumps(evidence, sort_keys=True),
            explanation=explanation,
            suggested_action=suggested_action,
            status=AnomalyStatus.OPEN
        )
        db.add(alert)
        db.flush()
        return alert

    @classmethod
    def scan_all_anomalies(cls, db: Session) -> List[AnomalyAlert]:
        """Runs a complete system scan detecting all 12 anomaly categories."""
        created_alerts: List[AnomalyAlert] = []

        # 1. Negative leave balance
        balances = db.query(LeaveBalance).all()
        for b in balances:
            avail = b.allocated_days - b.used_days - b.reserved_days
            if avail < 0 or b.allocated_days < 0 or b.used_days > b.allocated_days:
                alert = cls.record_alert(
                    db=db,
                    anomaly_type="NEGATIVE_LEAVE_BALANCE",
                    severity=AnomalySeverity.HIGH,
                    detection_method="Ledger Balance Audit",
                    explanation=f"Negative or overdrawn leave balance detected for employee {b.employee_id}: {avail:.1f} available days.",
                    suggested_action="Review past committed leave transactions and adjust policy allocation.",
                    evidence={"allocated": b.allocated_days, "used": b.used_days, "reserved": b.reserved_days, "available": avail},
                    employee_id=b.employee_id
                )
                created_alerts.append(alert)

        # 2. Overlapping approved leave
        approved_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.status == LeaveRequestStatus.APPROVED
        ).all()
        for i, l1 in enumerate(approved_leaves):
            for l2 in approved_leaves[i+1:]:
                if l1.employee_id == l2.employee_id and l1.start_date <= l2.end_date and l1.end_date >= l2.start_date:
                    alert = cls.record_alert(
                        db=db,
                        anomaly_type="OVERLAPPING_APPROVED_LEAVE",
                        severity=AnomalySeverity.CRITICAL,
                        detection_method="Interval Temporal Intersection",
                        explanation=f"Employee {l1.employee_id} has overlapping approved leave requests: {l1.id} and {l2.id}.",
                        suggested_action="Contact employee and cancel the duplicate/overlapping booking.",
                        evidence={"request_1": l1.id, "request_2": l2.id, "dates_1": [l1.start_date.isoformat(), l1.end_date.isoformat()], "dates_2": [l2.start_date.isoformat(), l2.end_date.isoformat()]},
                        request_id=l1.id,
                        employee_id=l1.employee_id
                    )
                    created_alerts.append(alert)

        # 3. Expense outside employment dates
        claims = db.query(ExpenseClaim).all()
        for c in claims:
            emp = db.query(Employee).filter(Employee.id == c.employee_id).first()
            if emp:
                if c.claim_date < emp.hire_date or (emp.termination_date and c.claim_date > emp.termination_date):
                    alert = cls.record_alert(
                        db=db,
                        anomaly_type="EXPENSE_OUTSIDE_EMPLOYMENT_DATES",
                        severity=AnomalySeverity.CRITICAL,
                        detection_method="Employment Tenure Boundary Check",
                        explanation=f"Expense {c.id} dated {c.claim_date} falls outside employee tenure (Hire: {emp.hire_date}, Term: {emp.termination_date}).",
                        suggested_action="Reject claim and notify Payroll/HR of out-of-tenure submission.",
                        evidence={"claim_date": c.claim_date.isoformat(), "hire_date": emp.hire_date.isoformat(), "termination_date": emp.termination_date.isoformat() if emp.termination_date else None},
                        request_id=c.id,
                        employee_id=c.employee_id
                    )
                    created_alerts.append(alert)

        # 4. Self-approval attempts
        approval_steps = db.query(ApprovalStep).all()
        for step in approval_steps:
            req_emp_id = None
            if step.request_type == "LEAVE":
                lr = db.query(LeaveRequest).filter(LeaveRequest.id == step.request_id).first()
                if lr: req_emp_id = lr.employee_id
            elif step.request_type == "EXPENSE":
                ec = db.query(ExpenseClaim).filter(ExpenseClaim.id == step.request_id).first()
                if ec: req_emp_id = ec.employee_id

            if req_emp_id and step.approver_id == req_emp_id:
                alert = cls.record_alert(
                    db=db,
                    anomaly_type="SELF_APPROVAL_DETECTED",
                    severity=AnomalySeverity.CRITICAL,
                    detection_method="Segregation of Duties Enforcement",
                    explanation=f"Approval step {step.id} has approver {step.approver_id} matching applicant {req_emp_id}.",
                    suggested_action="Revoke step and reassign to independent department head or manager.",
                    evidence={"step_id": step.id, "request_id": step.request_id, "approver_id": step.approver_id, "applicant_id": req_emp_id},
                    request_id=step.request_id,
                    employee_id=req_emp_id
                )
                created_alerts.append(alert)

        # 5. Duplicate reimbursement
        reimbursements = db.query(Reimbursement).all()
        seen_claims = {}
        for r in reimbursements:
            if r.claim_id in seen_claims:
                alert = cls.record_alert(
                    db=db,
                    anomaly_type="DUPLICATE_REIMBURSEMENT",
                    severity=AnomalySeverity.CRITICAL,
                    detection_method="Disbursement Ledger Audit",
                    explanation=f"Multiple reimbursements issued for single claim {r.claim_id}: {r.id} and {seen_claims[r.claim_id]}.",
                    suggested_action="Halt pending payment batches and audit finance settlement journal.",
                    evidence={"claim_id": r.claim_id, "reimbursement_1": r.id, "reimbursement_2": seen_claims[r.claim_id]},
                    request_id=r.claim_id
                )
                created_alerts.append(alert)
            else:
                seen_claims[r.claim_id] = r.id

        # 6. Missing cost center
        for c in claims:
            if not c.cost_center_id or not db.query(CostCenter).filter(CostCenter.id == c.cost_center_id).first():
                alert = cls.record_alert(
                    db=db,
                    anomaly_type="MISSING_COST_CENTER",
                    severity=AnomalySeverity.MEDIUM,
                    detection_method="Chart of Accounts Foreign Key Validation",
                    explanation=f"Expense claim {c.id} lacks a valid Cost Center association.",
                    suggested_action="Assign cost center before authorizing disbursement.",
                    evidence={"claim_id": c.id, "cost_center_id": c.cost_center_id},
                    request_id=c.id,
                    employee_id=c.employee_id
                )
                created_alerts.append(alert)

        # 7. Duplicate receipt hash
        seen_hashes = {}
        for c in claims:
            if c.receipt_hash and c.status not in [ExpenseClaimStatus.REJECTED, ExpenseClaimStatus.CANCELLED]:
                if c.receipt_hash in seen_hashes:
                    prior_id = seen_hashes[c.receipt_hash]
                    alert = cls.record_alert(
                        db=db,
                        anomaly_type="DUPLICATE_RECEIPT_HASH",
                        severity=AnomalySeverity.HIGH,
                        detection_method="Cryptographic SHA-256 Digest Collision",
                        explanation=f"Receipt for claim {c.id} matches identical file SHA-256 digest with claim {prior_id}.",
                        suggested_action="Review attached receipt images to verify if duplicate expense was claimed.",
                        evidence={"claim_id": c.id, "collided_with": prior_id, "receipt_hash": c.receipt_hash},
                        request_id=c.id,
                        employee_id=c.employee_id
                    )
                    created_alerts.append(alert)
                else:
                    seen_hashes[c.receipt_hash] = c.id

        # 8. Budget Overrun
        cost_centers = db.query(CostCenter).all()
        for cc in cost_centers:
            if cc.current_spend > cc.budget_limit:
                alert = cls.record_alert(
                    db=db,
                    anomaly_type="BUDGET_OVERRUN",
                    severity=AnomalySeverity.HIGH,
                    detection_method="Financial Threshold Variance",
                    explanation=f"Cost center {cc.code} spend (${cc.current_spend:,.2f}) exceeds allocated budget limit (${cc.budget_limit:,.2f}).",
                    suggested_action="Require Process Owner or Executive budget augmentation approval.",
                    evidence={"cost_center_id": cc.id, "budget_limit": float(cc.budget_limit), "current_spend": float(cc.current_spend)},
                    employee_id=None
                )
                created_alerts.append(alert)

        return created_alerts
