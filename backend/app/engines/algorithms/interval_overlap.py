from datetime import date
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from backend.app.models.leave import LeaveRequest, LeaveRequestStatus

def check_interval_overlap(
    db: Session,
    employee_id: str,
    start_date: date,
    end_date: date,
    current_request_id: Optional[str] = None
) -> Dict:
    """
    Detects if [start_date, end_date] overlaps with any active (submitted, pending, approved)
    leave request of the same employee.
    Two intervals [A, B] and [C, D] overlap if A <= D and B >= C.
    """
    query = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_([
            LeaveRequestStatus.SUBMITTED,
            LeaveRequestStatus.PENDING_APPROVAL,
            LeaveRequestStatus.APPROVED
        ]),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    )

    if current_request_id:
        query = query.filter(LeaveRequest.id != current_request_id)

    overlapping_requests = query.all()

    if overlapping_requests:
        conflicts = [
            {
                "request_id": req.id,
                "policy_id": req.leave_policy_id,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "status": req.status.value,
                "total_days": req.total_days
            }
            for req in overlapping_requests
        ]
        return {
            "has_overlap": True,
            "conflicts": conflicts,
            "message": f"Overlaps with {len(conflicts)} existing leave request(s): " + 
                       ", ".join(c["request_id"] for c in conflicts)
        }

    return {
        "has_overlap": False,
        "conflicts": [],
        "message": "No overlapping leave intervals found."
    }
