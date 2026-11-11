from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timezone
from backend.app.core.database import get_db
from backend.app.models.leave import LeavePolicy
from backend.app.models.expense import ExpensePolicy, ExpenseCategory
from backend.app.models.decision import RuleVersion
from backend.app.models.employee import Employee, EmployeeRole
from backend.app.api.deps import get_current_active_user, require_roles
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/policies", tags=["Policy & Rule Governance"])

@router.get("")
def get_all_policies(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    leave_policies = db.query(LeavePolicy).all()
    expense_policies = db.query(ExpensePolicy).all()
    versions = db.query(RuleVersion).order_by(RuleVersion.version_number.desc()).limit(10).all()

    return {
        "leave_policies": [
            {
                "id": lp.id,
                "code": lp.code,
                "name": lp.name,
                "days_per_year": lp.days_per_year,
                "max_consecutive_days": lp.max_consecutive_days,
                "carryover_allowed": lp.carryover_allowed,
                "documentation_required_days": lp.documentation_required_days,
                "employee_grade_min": lp.employee_grade_min,
                "description": lp.description
            }
            for lp in leave_policies
        ],
        "expense_policies": [
            {
                "id": ep.id,
                "category": ep.category.value,
                "max_per_claim": float(ep.max_per_claim),
                "daily_limit": float(ep.daily_limit),
                "receipt_required_above": float(ep.receipt_required_above),
                "currency": ep.currency,
                "description": ep.description
            }
            for ep in expense_policies
        ],
        "recent_versions": [
            {
                "id": v.id,
                "rule_type": v.rule_type,
                "version_number": v.version_number,
                "effective_date": v.effective_date.isoformat(),
                "created_by": v.created_by,
                "description": v.description
            }
            for v in versions
        ]
    }

@router.post("/leave/{id}")
def update_leave_policy(
    id: str,
    days_per_year: float,
    max_consecutive_days: int,
    documentation_required_days: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    lp = db.query(LeavePolicy).filter(LeavePolicy.id == id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Leave policy not found")

    old_config = {
        "days_per_year": lp.days_per_year,
        "max_consecutive_days": lp.max_consecutive_days,
        "documentation_required_days": lp.documentation_required_days
    }

    lp.days_per_year = days_per_year
    lp.max_consecutive_days = max_consecutive_days
    lp.documentation_required_days = documentation_required_days

    # Version tracking
    v_count = db.query(RuleVersion).filter(RuleVersion.rule_type == "LEAVE_POLICY").count()
    version = RuleVersion(
        rule_type="LEAVE_POLICY",
        version_number=v_count + 1,
        configuration_json=json.dumps({"id": id, "old": old_config, "new": {"days_per_year": days_per_year, "max_consecutive_days": max_consecutive_days}}),
        created_by=current_user.id,
        description=f"Updated policy {lp.name} thresholds"
    )
    db.add(version)

    AuditService.record_event(
        db=db,
        entity_type="POLICY",
        entity_id=lp.id,
        action="POLICY_UPDATED",
        payload={"policy_code": lp.code, "version": v_count + 1, "updated_by": current_user.id},
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Leave policy {lp.name} updated to version {v_count + 1}."}

@router.post("/expense/{id}")
def update_expense_policy(
    id: str,
    max_per_claim: float,
    daily_limit: float,
    receipt_required_above: float,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles([EmployeeRole.PROCESS_OWNER, EmployeeRole.ADMIN]))
):
    ep = db.query(ExpensePolicy).filter(ExpensePolicy.id == id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Expense policy not found")

    old_config = {
        "max_per_claim": float(ep.max_per_claim),
        "daily_limit": float(ep.daily_limit),
        "receipt_required_above": float(ep.receipt_required_above)
    }

    ep.max_per_claim = max_per_claim
    ep.daily_limit = daily_limit
    ep.receipt_required_above = receipt_required_above

    v_count = db.query(RuleVersion).filter(RuleVersion.rule_type == "EXPENSE_POLICY").count()
    version = RuleVersion(
        rule_type="EXPENSE_POLICY",
        version_number=v_count + 1,
        configuration_json=json.dumps({"id": id, "old": old_config, "new": {"max_per_claim": max_per_claim, "daily_limit": daily_limit}}),
        created_by=current_user.id,
        description=f"Updated policy {ep.category.value} caps"
    )
    db.add(version)

    AuditService.record_event(
        db=db,
        entity_type="POLICY",
        entity_id=ep.id,
        action="POLICY_UPDATED",
        payload={"category": ep.category.value, "version": v_count + 1, "updated_by": current_user.id},
        actor_id=current_user.id
    )

    db.commit()
    return {"message": f"Expense policy {ep.category.value} updated to version {v_count + 1}."}
