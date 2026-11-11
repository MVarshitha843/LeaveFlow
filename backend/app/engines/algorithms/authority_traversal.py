from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.app.models.employee import Employee, EmployeeRole, Department
from backend.app.core.config import settings

def resolve_approval_chain(
    db: Session,
    employee_id: str,
    request_type: str,  # "LEAVE" or "EXPENSE"
    amount_or_days: float,
    category: Optional[str] = None
) -> List[Dict]:
    """
    Traverses the organizational authority graph to construct an ordered approval chain.
    CRITICAL INVARIANT: Zero Self-Approval. An employee can NEVER approve their own request.
    If the immediate manager is the employee or missing, traverses upward or assigns
    an authorized corporate role (Finance or Admin).
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} not found")

    approval_chain: List[Dict] = []
    seen_approvers = {employee_id}  # prevent self-approval and duplicate steps

    # Step 1: Direct Manager
    direct_manager = None
    if employee.manager_id and employee.manager_id != employee_id:
        direct_manager = db.query(Employee).filter(
            Employee.id == employee.manager_id,
            Employee.status == "ACTIVE"
        ).first()

    # If employee has no direct manager or is the top manager, route to Department Head or Admin
    if not direct_manager or direct_manager.id in seen_approvers:
        # Try Department Head
        if employee.department_id:
            dept = db.query(Department).filter(Department.id == employee.department_id).first()
            if dept and dept.head_id and dept.head_id not in seen_approvers:
                direct_manager = db.query(Employee).filter(
                    Employee.id == dept.head_id,
                    Employee.status == "ACTIVE"
                ).first()

    # Fallback to an active Admin/Manager if still none found
    if not direct_manager or direct_manager.id in seen_approvers:
        direct_manager = db.query(Employee).filter(
            Employee.role.in_([EmployeeRole.ADMIN, EmployeeRole.PROCESS_OWNER]),
            Employee.id != employee_id,
            Employee.status == "ACTIVE"
        ).first()

    if direct_manager and direct_manager.id not in seen_approvers:
        approval_chain.append({
            "step_order": 1,
            "approver_id": direct_manager.id,
            "approver_name": f"{direct_manager.first_name} {direct_manager.last_name}",
            "approver_role": direct_manager.role.value,
            "stage_name": "Direct Manager Review"
        })
        seen_approvers.add(direct_manager.id)

    # Secondary steps based on request type and thresholds
    if request_type == "LEAVE":
        # Leave requests > 10 business days require Department Head approval
        if amount_or_days > 10.0 and employee.department_id:
            dept = db.query(Department).filter(Department.id == employee.department_id).first()
            if dept and dept.head_id and dept.head_id not in seen_approvers:
                head = db.query(Employee).filter(
                    Employee.id == dept.head_id,
                    Employee.status == "ACTIVE"
                ).first()
                if head:
                    approval_chain.append({
                        "step_order": len(approval_chain) + 1,
                        "approver_id": head.id,
                        "approver_name": f"{head.first_name} {head.last_name}",
                        "approver_role": head.role.value,
                        "stage_name": "Department Head Review (>10 Days)"
                    })
                    seen_approvers.add(head.id)

    elif request_type == "EXPENSE":
        amount_dec = Decimal(str(amount_or_days))
        # Claims > $1,000 require Finance review
        if amount_dec >= Decimal(str(settings.EXPENSE_MANAGER_THRESHOLD)):
            finance_approver = db.query(Employee).filter(
                Employee.role == EmployeeRole.FINANCE,
                Employee.id != employee_id,
                Employee.status == "ACTIVE"
            ).first()
            if finance_approver and finance_approver.id not in seen_approvers:
                approval_chain.append({
                    "step_order": len(approval_chain) + 1,
                    "approver_id": finance_approver.id,
                    "approver_name": f"{finance_approver.first_name} {finance_approver.last_name}",
                    "approver_role": "FINANCE",
                    "stage_name": "Finance Review (High Value Threshold)"
                })
                seen_approvers.add(finance_approver.id)

        # High-value claims > $5,000 require Executive/Admin approval
        if amount_dec >= Decimal("5000.00"):
            admin_approver = db.query(Employee).filter(
                Employee.role == EmployeeRole.ADMIN,
                Employee.id != employee_id,
                Employee.status == "ACTIVE"
            ).first()
            if admin_approver and admin_approver.id not in seen_approvers:
                approval_chain.append({
                    "step_order": len(approval_chain) + 1,
                    "approver_id": admin_approver.id,
                    "approver_name": f"{admin_approver.first_name} {admin_approver.last_name}",
                    "approver_role": "ADMIN",
                    "stage_name": "Executive Approval (> $5,000)"
                })
                seen_approvers.add(admin_approver.id)

    # Verification: Ensure no step allows self-approval
    for step in approval_chain:
        assert step["approver_id"] != employee_id, f"CRITICAL: Self-approval detected for {employee_id}"

    return approval_chain
