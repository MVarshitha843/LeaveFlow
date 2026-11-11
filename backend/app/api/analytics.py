from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timezone
from backend.app.core.database import get_db
from backend.app.models.employee import Employee, Department, CostCenter
from backend.app.models.leave import LeaveRequest, LeaveRequestStatus, DecisionState, LeavePolicy, LeaveBalance
from backend.app.models.expense import ExpenseClaim, ExpenseClaimStatus
from backend.app.models.approval import ApprovalStep, ApprovalStepStatus, Reimbursement, ReimbursementStatus
from backend.app.models.anomaly import AnomalyAlert, AnomalyStatus
from backend.app.schemas.analytics import AnalyticsOverviewResponse
from backend.app.api.deps import get_current_active_user

router = APIRouter(prefix="/analytics", tags=["Dashboard Analytics Engine"])

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    # 1. Total counts
    total_employees = db.query(Employee).count()
    total_leave = db.query(LeaveRequest).count()
    total_expenses = db.query(ExpenseClaim).count()

    # Approvals
    pending_approvals = db.query(ApprovalStep).filter(
        ApprovalStep.status == ApprovalStepStatus.PENDING
    ).count()

    # Status breakdowns
    approved_leave = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveRequestStatus.APPROVED).count()
    approved_expense = db.query(ExpenseClaim).filter(ExpenseClaim.status.in_([ExpenseClaimStatus.APPROVED, ExpenseClaimStatus.REIMBURSED])).count()
    approved_requests = approved_leave + approved_expense

    rejected_leave = db.query(LeaveRequest).filter(LeaveRequest.status == LeaveRequestStatus.REJECTED).count()
    rejected_expense = db.query(ExpenseClaim).filter(ExpenseClaim.status == ExpenseClaimStatus.REJECTED).count()
    rejected_requests = rejected_leave + rejected_expense

    review_leave = db.query(LeaveRequest).filter(LeaveRequest.decision_state == DecisionState.NEEDS_REVIEW).count()
    review_expense = db.query(ExpenseClaim).filter(ExpenseClaim.decision_state == DecisionState.NEEDS_REVIEW).count()
    needs_review_requests = review_leave + review_expense

    # Financial sums
    expense_sum_query = db.query(func.sum(ExpenseClaim.total_amount)).scalar()
    total_expense_amount = float(expense_sum_query) if expense_sum_query else 0.0

    reimbursed_sum_query = db.query(func.sum(Reimbursement.amount)).filter(
        Reimbursement.status == ReimbursementStatus.PROCESSED
    ).scalar()
    total_reimbursed_amount = float(reimbursed_sum_query) if reimbursed_sum_query else 0.0

    # Budget & Leave utilization
    dept_budget_total = db.query(func.sum(Department.annual_budget)).scalar() or 1.0
    dept_spend_total = db.query(func.sum(Department.current_spend)).scalar() or 0.0
    budget_utilization_pct = round((float(dept_spend_total) / float(dept_budget_total)) * 100, 2)

    allocated_leave_sum = db.query(func.sum(LeaveBalance.allocated_days)).scalar() or 1.0
    used_leave_sum = db.query(func.sum(LeaveBalance.used_days)).scalar() or 0.0
    leave_utilization_pct = round((float(used_leave_sum) / float(allocated_leave_sum)) * 100, 2)

    # Anomalies
    open_anomalies_count = db.query(AnomalyAlert).filter(
        AnomalyAlert.status.in_([AnomalyStatus.OPEN, AnomalyStatus.UNDER_REVIEW])
    ).count()

    dup_receipts = db.query(AnomalyAlert).filter(
        AnomalyAlert.anomaly_type == "DUPLICATE_RECEIPT_HASH"
    ).count()

    split_claims = db.query(AnomalyAlert).filter(
        AnomalyAlert.anomaly_type == "ROLLING_WINDOW_SPLIT_CLAIM"
    ).count()

    # Average approval time (in hours)
    completed_steps = db.query(ApprovalStep).filter(
        ApprovalStep.action_timestamp.isnot(None),
        ApprovalStep.status.in_([ApprovalStepStatus.APPROVED, ApprovalStepStatus.REJECTED])
    ).all()

    turnaround_times = [
        (s.action_timestamp - s.created_at).total_seconds() / 3600.0
        for s in completed_steps
        if s.action_timestamp and s.action_timestamp >= s.created_at
    ]
    avg_turnaround_hours = round(sum(turnaround_times) / len(turnaround_times), 1) if turnaround_times else 3.5

    # 1. Monthly Leave Trends
    leave_records = db.query(LeaveRequest.created_at, LeaveRequest.business_days).all()
    monthly_leave = defaultdict(lambda: {"count": 0, "days": 0.0})
    for l_dt, b_days in leave_records:
        if l_dt:
            month_key = l_dt.strftime("%b %Y")
            monthly_leave[month_key]["count"] += 1
            monthly_leave[month_key]["days"] += float(b_days)

    monthly_leave_trends = [
        {"month": m, "requests": d["count"], "days": round(d["days"], 1)}
        for m, d in list(monthly_leave.items())[-6:]
    ]
    if not monthly_leave_trends:
        monthly_leave_trends = [{"month": "Nov 2026", "requests": total_leave, "days": float(used_leave_sum)}]

    # 2. Monthly Expense Trends
    expense_records = db.query(ExpenseClaim.created_at, ExpenseClaim.total_amount).all()
    monthly_exp = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for e_dt, amt in expense_records:
        if e_dt:
            month_key = e_dt.strftime("%b %Y")
            monthly_exp[month_key]["count"] += 1
            monthly_exp[month_key]["amount"] += float(amt)

    monthly_expense_trends = [
        {"month": m, "claims": d["count"], "amount": round(d["amount"], 2)}
        for m, d in list(monthly_exp.items())[-6:]
    ]
    if not monthly_expense_trends:
        monthly_expense_trends = [{"month": "Nov 2026", "claims": total_expenses, "amount": total_expense_amount}]

    # 3. Department Expense Distribution
    departments = db.query(Department).all()
    department_expense_dist = []
    budget_utilization_by_dept = []
    for dept in departments:
        spend = float(dept.current_spend)
        budget = float(dept.annual_budget)
        pct = round((spend / budget) * 100, 1) if budget > 0 else 0.0
        department_expense_dist.append({"name": dept.name, "value": spend})
        budget_utilization_by_dept.append({"department": dept.code, "spend": spend, "budget": budget, "utilization_pct": pct})

    # 4. Approval Status Distribution
    approval_status_dist = [
        {"name": "Approved", "value": approved_requests, "color": "#16A34A"},
        {"name": "Pending Approval", "value": pending_approvals, "color": "#2563EB"},
        {"name": "Needs Review", "value": needs_review_requests, "color": "#D97706"},
        {"name": "Rejected", "value": rejected_requests, "color": "#DC2626"}
    ]

    # 5. Anomaly Category Distribution
    anomalies = db.query(AnomalyAlert.anomaly_type, func.count(AnomalyAlert.id)).group_by(AnomalyAlert.anomaly_type).all()
    anomaly_category_dist = [
        {"name": a_type.replace("_", " ").title(), "value": count}
        for a_type, count in anomalies
    ]

    # 6. Leave Type Distribution
    leave_types = db.query(LeavePolicy.name, func.count(LeaveRequest.id)).join(
        LeaveRequest, LeaveRequest.leave_policy_id == LeavePolicy.id
    ).group_by(LeavePolicy.name).all()

    leave_type_dist = [
        {"name": p_name, "value": count}
        for p_name, count in leave_types
    ]
    if not leave_type_dist:
        leave_type_dist = [{"name": "Annual Leave", "value": total_leave}]

    return AnalyticsOverviewResponse(
        total_employees=total_employees,
        total_leave_requests=total_leave,
        total_expense_claims=total_expenses,
        pending_approvals=pending_approvals,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests,
        needs_review_requests=needs_review_requests,
        total_expense_amount=total_expense_amount,
        total_reimbursed_amount=total_reimbursed_amount,
        budget_utilization_pct=budget_utilization_pct,
        leave_utilization_pct=leave_utilization_pct,
        open_anomalies_count=open_anomalies_count,
        duplicate_receipt_alerts=dup_receipts,
        split_claim_alerts=split_claims,
        avg_approval_time_hours=avg_turnaround_hours,
        monthly_leave_trends=monthly_leave_trends,
        monthly_expense_trends=monthly_expense_trends,
        department_expense_dist=department_expense_dist,
        budget_utilization_by_dept=budget_utilization_by_dept,
        approval_status_dist=approval_status_dist,
        anomaly_category_dist=anomaly_category_dist,
        leave_type_dist=leave_type_dist
    )
