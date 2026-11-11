from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalyticsOverviewResponse(BaseModel):
    total_employees: int
    total_leave_requests: int
    total_expense_claims: int
    pending_approvals: int
    approved_requests: int
    rejected_requests: int
    needs_review_requests: int
    total_expense_amount: float
    total_reimbursed_amount: float
    budget_utilization_pct: float
    leave_utilization_pct: float
    open_anomalies_count: int
    duplicate_receipt_alerts: int
    split_claim_alerts: int
    avg_approval_time_hours: float
    
    # Chart series
    monthly_leave_trends: List[Dict[str, Any]]
    monthly_expense_trends: List[Dict[str, Any]]
    department_expense_dist: List[Dict[str, Any]]
    budget_utilization_by_dept: List[Dict[str, Any]]
    approval_status_dist: List[Dict[str, Any]]
    anomaly_category_dist: List[Dict[str, Any]]
    leave_type_dist: List[Dict[str, Any]]
