export type Role = 'EMPLOYEE' | 'MANAGER' | 'FINANCE' | 'PROCESS_OWNER' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  department_id?: string;
  manager_id?: string;
  grade: string;
  country: string;
  status: string;
  hire_date: string;
}

export interface LeavePolicy {
  id: string;
  code: string;
  name: string;
  days_per_year: number;
  max_consecutive_days: number;
  carryover_allowed: number;
  documentation_required_days: number;
  employee_grade_min: string;
  description?: string;
}

export interface LeaveBalance {
  id: number;
  employee_id: string;
  leave_policy_id: string;
  policy_name?: string;
  year: number;
  allocated_days: number;
  used_days: number;
  reserved_days: number;
  available_days: number;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name?: string;
  leave_policy_id: string;
  policy_name?: string;
  start_date: string;
  end_date: string;
  total_days: number;
  business_days: number;
  reason: string;
  document_url?: string;
  status: 'SUBMITTED' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  decision_state: 'ELIGIBLE' | 'NEEDS_REVIEW' | 'BLOCKED';
  decision_explanation?: string;
  created_at: string;
  updated_at: string;
}

export interface ExpensePolicy {
  id: string;
  category: string;
  max_per_claim: number;
  daily_limit: number;
  receipt_required_above: number;
  currency: string;
  description?: string;
}

export interface ExpenseLine {
  id: string;
  claim_id: string;
  line_number: number;
  category: string;
  description: string;
  amount: number;
  receipt_hash?: string;
}

export interface ExpenseClaim {
  id: string;
  employee_id: string;
  employee_name?: string;
  cost_center_id: string;
  cost_center_name?: string;
  category: string;
  merchant: string;
  claim_date: string;
  total_amount: number;
  currency: string;
  description: string;
  receipt_url?: string;
  receipt_hash?: string;
  status: 'SUBMITTED' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'CANCELLED' | 'REIMBURSED';
  decision_state: 'ELIGIBLE' | 'NEEDS_REVIEW' | 'BLOCKED';
  decision_explanation?: string;
  lines: ExpenseLine[];
  created_at: string;
  updated_at: string;
}

export interface ApprovalStep {
  id: string;
  request_id: string;
  request_type: string;
  approver_id: string;
  approver_name?: string;
  approver_role?: string;
  step_order: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'INFO_REQUESTED';
  comments?: string;
  action_timestamp?: string;
  created_at: string;
}

export interface PendingApprovalItem {
  step_id: string;
  request_id: string;
  request_type: string;
  step_order: number;
  status: string;
  applicant_id: string;
  applicant_name: string;
  approver_id: string;
  approver_name: string;
  amount_or_days: number;
  summary: string;
  created_at: string;
}

export interface AnomalyAlert {
  id: number;
  anomaly_type: string;
  request_id?: string;
  employee_id?: string;
  employee_name?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  detection_method: string;
  evidence_json: string;
  explanation: string;
  suggested_action?: string;
  status: 'OPEN' | 'UNDER_REVIEW' | 'CONFIRMED' | 'DISMISSED' | 'RESOLVED';
  resolved_by?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id?: string;
  previous_hash: string;
  current_hash: string;
  payload_json: string;
  timestamp: string;
}

export interface NotificationItem {
  id: number;
  recipient_id: string;
  title: string;
  message: string;
  category: string;
  is_read: number;
  link_url?: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  name: string;
  description: string;
  category: string;
  is_blocking: boolean;
  dependencies: string[];
  status: 'PASS' | 'FAIL' | 'REVIEW' | 'NOT_EVALUATED';
  executed: boolean;
  execution_time_ms: number;
  evidence?: {
    result: string;
    actual_condition: string;
    expected_condition: string;
    evidence_source: string;
    reason: string;
    timestamp: string;
    details?: any;
  };
}

export interface EFCGGraph {
  request_id: string;
  request_type: string;
  decision_state: string;
  explanation: string;
  summary: {
    total_constraints: number;
    passed: number;
    failed_blocking: number;
    failed_non_blocking: number;
    review_required: number;
  };
  nodes: GraphNode[];
  edges: { source: string; target: string }[];
  execution_order: string[];
}

export interface Department {
  id: string;
  code: string;
  name: string;
  head_id?: string;
  annual_budget: number;
  current_spend: number;
  reserved_budget: number;
  available_budget: number;
}

export interface CostCenter {
  id: string;
  code: string;
  name: string;
  department_id: string;
  budget_limit: number;
  current_spend: number;
  reserved_spend: number;
  available_spend: number;
}

export interface AnalyticsOverview {
  total_employees: number;
  total_leave_requests: number;
  total_expense_claims: number;
  pending_approvals: number;
  approved_requests: number;
  rejected_requests: number;
  needs_review_requests: number;
  total_expense_amount: number;
  total_reimbursed_amount: number;
  budget_utilization_pct: number;
  leave_utilization_pct: number;
  open_anomalies_count: number;
  duplicate_receipt_alerts: number;
  split_claim_alerts: number;
  avg_approval_time_hours: number;
  monthly_leave_trends: any[];
  monthly_expense_trends: any[];
  department_expense_dist: any[];
  budget_utilization_by_dept: any[];
  approval_status_dist: any[];
  anomaly_category_dist: any[];
  leave_type_dist: any[];
}
