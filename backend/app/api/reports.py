import io
import csv
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.leave import LeaveRequest
from backend.app.models.expense import ExpenseClaim
from backend.app.models.approval import ApprovalStep
from backend.app.models.anomaly import AnomalyAlert
from backend.app.models.audit import AuditEvent
from backend.app.models.employee import Employee, EmployeeRole
from backend.app.api.deps import get_current_active_user, require_roles

router = APIRouter(prefix="/reports", tags=["Reports & Data Exports"])

@router.get("/leave-csv")
def export_leave_csv(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.MANAGER, EmployeeRole.FINANCE, EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Request_ID", "Employee_ID", "Policy_ID", "Start_Date", "End_Date",
        "Total_Days", "Business_Days", "Status", "Decision_State", "Created_At"
    ])

    requests = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
    for r in requests:
        writer.writerow([
            r.id, r.employee_id, r.leave_policy_id, r.start_date.isoformat(),
            r.end_date.isoformat(), r.total_days, r.business_days,
            r.status.value, r.decision_state.value, r.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaveflow_leave_requests.csv"}
    )

@router.get("/expense-csv")
def export_expense_csv(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.FINANCE, EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Claim_ID", "Employee_ID", "Cost_Center_ID", "Category", "Merchant",
        "Claim_Date", "Total_Amount", "Currency", "Status", "Decision_State", "Receipt_Hash", "Created_At"
    ])

    claims = db.query(ExpenseClaim).order_by(ExpenseClaim.created_at.desc()).all()
    for c in claims:
        writer.writerow([
            c.id, c.employee_id, c.cost_center_id, c.category.value, c.merchant,
            c.claim_date.isoformat(), float(c.total_amount), c.currency,
            c.status.value, c.decision_state.value, c.receipt_hash or "", c.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaveflow_expense_claims.csv"}
    )

@router.get("/audit-csv")
def export_audit_csv(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.ADMIN, EmployeeRole.PROCESS_OWNER]))
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event_ID", "Entity_Type", "Entity_ID", "Action", "Actor_ID",
        "Previous_Hash", "Current_Hash", "Timestamp"
    ])

    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    for e in events:
        writer.writerow([
            e.id, e.entity_type, e.entity_id, e.action, e.actor_id,
            e.previous_hash, e.current_hash, e.timestamp.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaveflow_audit_trail.csv"}
    )

@router.get("/anomalies-csv")
def export_anomalies_csv(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.FINANCE, EmployeeRole.ADMIN]))
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Alert_ID", "Anomaly_Type", "Severity", "Request_ID", "Employee_ID",
        "Detection_Method", "Status", "Created_At"
    ])

    alerts = db.query(AnomalyAlert).order_by(AnomalyAlert.created_at.desc()).all()
    for a in alerts:
        writer.writerow([
            a.id, a.anomaly_type, a.severity.value, a.request_id or "", a.employee_id or "",
            a.detection_method, a.status.value, a.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaveflow_anomalies.csv"}
    )

@router.get("/ground-truth")
def export_ground_truth(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.ADMIN]))
):
    """
    Restricted export of ground truth anomaly manifest.
    Strictly isolated from normal decision engine operations.
    """
    gt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ground_truth", "ground_truth_manifest.json"))
    if not os.path.exists(gt_path):
        return {"message": "Ground truth manifest not yet generated. Run scripts/generate_data.py first."}

    with open(gt_path, "r") as f:
        data = json.load(f)
    return data
