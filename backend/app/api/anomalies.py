from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.core.database import get_db
from backend.app.models.anomaly import AnomalyAlert, AnomalySeverity, AnomalyStatus
from backend.app.models.employee import Employee, EmployeeRole
from backend.app.schemas.anomaly import AnomalyAlertResponse, AnomalyReviewRequest
from backend.app.api.deps import get_current_active_user, require_roles
from backend.app.engines.anomaly.detector import AnomalyDetector
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/anomalies", tags=["Anomaly Review Queue"])

@router.get("", response_model=List[AnomalyAlertResponse])
def list_anomalies(
    status: Optional[AnomalyStatus] = None,
    severity: Optional[AnomalySeverity] = None,
    anomaly_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(AnomalyAlert)
    if status:
        query = query.filter(AnomalyAlert.status == status)
    if severity:
        query = query.filter(AnomalyAlert.severity == severity)
    if anomaly_type:
        query = query.filter(AnomalyAlert.anomaly_type == anomaly_type)

    alerts = query.order_by(AnomalyAlert.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for a in alerts:
        emp_name = f"{a.employee.first_name} {a.employee.last_name}" if a.employee else a.employee_id
        results.append(AnomalyAlertResponse(
            id=a.id,
            anomaly_type=a.anomaly_type,
            request_id=a.request_id,
            employee_id=a.employee_id,
            employee_name=emp_name,
            severity=a.severity,
            detection_method=a.detection_method,
            evidence_json=a.evidence_json,
            explanation=a.explanation,
            suggested_action=a.suggested_action,
            status=a.status,
            resolved_by=a.resolved_by,
            created_at=a.created_at,
            updated_at=a.updated_at
        ))
    return results

@router.post("/scan")
def trigger_anomaly_scan(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.FINANCE, EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    """
    Executes a comprehensive system-wide scan across all 12 anomaly classifications.
    """
    new_alerts = AnomalyDetector.scan_all_anomalies(db)
    db.commit()
    return {
        "message": f"Anomaly detection scan complete. Processed {len(new_alerts)} active alerts.",
        "new_alerts_detected": len(new_alerts)
    }

@router.post("/{id}/review", response_model=AnomalyAlertResponse)
def review_anomaly(
    id: int,
    body: AnomalyReviewRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.FINANCE, EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    alert = db.query(AnomalyAlert).filter(AnomalyAlert.id == id).with_for_update().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")

    old_status = alert.status
    alert.status = body.status
    alert.resolved_by = current_user.id
    alert.updated_at = datetime.now(timezone.utc)

    AuditService.record_event(
        db=db,
        entity_type="ANOMALY_ALERT",
        entity_id=str(alert.id),
        action="STATUS_CHANGED",
        payload={
            "anomaly_type": alert.anomaly_type,
            "old_status": old_status.value,
            "new_status": body.status.value,
            "reviewed_by": current_user.id,
            "notes": body.notes
        },
        actor_id=current_user.id
    )

    db.commit()
    db.refresh(alert)

    emp_name = f"{alert.employee.first_name} {alert.employee.last_name}" if alert.employee else alert.employee_id
    return AnomalyAlertResponse(
        id=alert.id,
        anomaly_type=alert.anomaly_type,
        request_id=alert.request_id,
        employee_id=alert.employee_id,
        employee_name=emp_name,
        severity=alert.severity,
        detection_method=alert.detection_method,
        evidence_json=alert.evidence_json,
        explanation=alert.explanation,
        suggested_action=alert.suggested_action,
        status=alert.status,
        resolved_by=alert.resolved_by,
        created_at=alert.created_at,
        updated_at=alert.updated_at
    )
