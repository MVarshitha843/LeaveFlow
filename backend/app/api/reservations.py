from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.ledger import ResourceReservation, ResourceType, ReservationStatus
from backend.app.models.employee import Employee
from backend.app.api.deps import get_current_active_user

router = APIRouter(prefix="/reservations", tags=["Resource Reservation Ledger"])

@router.get("")
def list_reservations(
    resource_type: Optional[ResourceType] = None,
    status: Optional[ReservationStatus] = None,
    request_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(ResourceReservation)
    if resource_type:
        query = query.filter(ResourceReservation.resource_type == resource_type)
    if status:
        query = query.filter(ResourceReservation.status == status)
    if request_id:
        query = query.filter(ResourceReservation.request_id == request_id)

    reservations = query.order_by(ResourceReservation.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for r in reservations:
        emp_name = f"{r.employee.first_name} {r.employee.last_name}" if r.employee else r.employee_id
        results.append({
            "id": r.id,
            "request_id": r.request_id,
            "resource_type": r.resource_type.value,
            "employee_id": r.employee_id,
            "employee_name": emp_name,
            "cost_center_id": r.cost_center_id,
            "leave_policy_id": r.leave_policy_id,
            "reserved_amount": float(r.reserved_amount),
            "previous_available": float(r.previous_available),
            "final_committed": float(r.final_committed),
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat()
        })
    return results

@router.get("/{id}")
def get_reservation(
    id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    r = db.query(ResourceReservation).filter(ResourceReservation.id == id).first()
    if not r:
        return {"error": "Reservation record not found"}
    emp_name = f"{r.employee.first_name} {r.employee.last_name}" if r.employee else r.employee_id
    return {
        "id": r.id,
        "request_id": r.request_id,
        "resource_type": r.resource_type.value,
        "employee_id": r.employee_id,
        "employee_name": emp_name,
        "cost_center_id": r.cost_center_id,
        "leave_policy_id": r.leave_policy_id,
        "reserved_amount": float(r.reserved_amount),
        "previous_available": float(r.previous_available),
        "final_committed": float(r.final_committed),
        "status": r.status.value,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat()
    }
