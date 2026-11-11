from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.employee import Employee
from backend.app.schemas.audit import AuditEventResponse, AuditVerifyResponse
from backend.app.api.deps import get_current_active_user
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])

@router.get("/events", response_model=List[AuditEventResponse])
def list_audit_events(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)

    return query.order_by(AuditEvent.id.desc()).offset(skip).limit(limit).all()

@router.get("/request/{request_id}", response_model=List[AuditEventResponse])
def get_request_audit_trail(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    return db.query(AuditEvent).filter(
        AuditEvent.entity_id == request_id
    ).order_by(AuditEvent.id.asc()).all()

@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_chain_integrity(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    """
    Cryptographic verification endpoint.
    Recalculates every SHA-256 block hash from genesis to head,
    verifying link pointers and canonical payload signatures.
    """
    res = AuditService.verify_integrity(db)
    return AuditVerifyResponse(
        is_valid=res["is_valid"],
        total_events=res["total_events"],
        head_hash=res.get("head_hash"),
        corrupted_event_id=res.get("corrupted_event_id"),
        error_type=res.get("error_type"),
        message=res["message"]
    )
