# LeaveFlow Data Dictionary (20 Relational Entities)

This data dictionary defines all normalized database models implemented for LeaveFlow.

---

### 1. `employees`
- `id` (VARCHAR(50), PK): Unique employee ID (e.g. `EMP-000001`).
- `email` (VARCHAR(150), UNIQUE, INDEX): Login email address.
- `hashed_password` (VARCHAR(255)): PBKDF2/Bcrypt hash.
- `first_name` (VARCHAR(50)): First name.
- `last_name` (VARCHAR(50)): Last name.
- `role` (ENUM): `EMPLOYEE`, `MANAGER`, `FINANCE`, `PROCESS_OWNER`, `ADMIN`.
- `department_id` (VARCHAR(50), FK -> `departments.id`): Primary department.
- `manager_id` (VARCHAR(50), FK -> `employees.id`): Direct supervisor.
- `hire_date` (DATE): Date of hire for tenure verification.
- `termination_date` (DATE, NULL): Date of separation if applicable.
- `grade` (VARCHAR(20)): Corporate seniority grade (`L1` to `EXEC`).
- `country` (VARCHAR(50)): Country of employment (`US`).
- `status` (ENUM): `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `TERMINATED`.
- `created_at` (DATETIME): UTC creation timestamp.

### 2. `departments`
- `id` (VARCHAR(50), PK): Department ID (e.g. `DEP-ENG`).
- `code` (VARCHAR(20), UNIQUE): Department code (`ENG`, `SALES`, `FIN`).
- `name` (VARCHAR(100)): Full department title.
- `head_id` (VARCHAR(50)): Employee ID of Department Head.
- `annual_budget` (DECIMAL(12,2)): Fiscal operating budget allocation.
- `current_spend` (DECIMAL(12,2)): Cumulative committed expenditures.
- `reserved_budget` (DECIMAL(12,2)): Pre-allocated funds held in reservation ledger.
- `created_at` (DATETIME): UTC creation timestamp.

### 3. `cost_centers`
- `id` (VARCHAR(50), PK): Cost center ID (e.g. `CC-ENG-01`).
- `code` (VARCHAR(20), UNIQUE): Cost center ledger code.
- `name` (VARCHAR(100)): Descriptive cost center name.
- `department_id` (VARCHAR(50), FK -> `departments.id`): Parent department.
- `budget_limit` (DECIMAL(12,2)): Line-item budget cap.
- `current_spend` (DECIMAL(12,2)): Consumed budget.
- `reserved_spend` (DECIMAL(12,2)): Reserved budget for pending claims.
- `created_at` (DATETIME): UTC creation timestamp.

### 4. `employee_cost_centers`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `employee_id` (VARCHAR(50), FK -> `employees.id`)
- `cost_center_id` (VARCHAR(50), FK -> `cost_centers.id`)
- `is_default` (INTEGER): Default cost center indicator (1 or 0).

### 5. `leave_policies`
- `id` (VARCHAR(50), PK): Policy ID (e.g. `POL-ANNUAL`).
- `code` (VARCHAR(20), UNIQUE): Unique policy code.
- `name` (VARCHAR(100)): Policy title.
- `days_per_year` (FLOAT): Annual entitlement allowance.
- `max_consecutive_days` (INTEGER): Maximum contiguous duration.
- `carryover_allowed` (INTEGER): Permitted year-end rollover days.
- `documentation_required_days` (INTEGER): Absence threshold requiring doctor's note/certificate.
- `employee_grade_min` (VARCHAR(20)): Grade eligibility threshold.
- `description` (TEXT): Policy handbook text.

### 6. `leave_balances`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `employee_id` (VARCHAR(50), FK -> `employees.id`, INDEX)
- `leave_policy_id` (VARCHAR(50), FK -> `leave_policies.id`)
- `year` (INTEGER): Entitlement year (e.g. 2026).
- `allocated_days` (FLOAT): Total granted entitlement.
- `used_days` (FLOAT): Approved and deducted days.
- `reserved_days` (FLOAT): Held in reservation ledger for pending requests.

### 7. `leave_requests`
- `id` (VARCHAR(50), PK): Leave ID (e.g. `LVE-2026-000001`).
- `employee_id` (VARCHAR(50), FK -> `employees.id`, INDEX)
- `leave_policy_id` (VARCHAR(50), FK -> `leave_policies.id`)
- `start_date` (DATE): First day of absence.
- `end_date` (DATE): Last day of absence.
- `total_days` (FLOAT): Total calendar days.
- `business_days` (FLOAT): Working days excluding weekends and statutory holidays.
- `reason` (TEXT): Justification text.
- `document_url` (VARCHAR(255)): Attached certificate path.
- `status` (ENUM): `SUBMITTED`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `CANCELLED`.
- `decision_state` (ENUM): `ELIGIBLE`, `NEEDS_REVIEW`, `BLOCKED`.
- `decision_explanation` (TEXT): Synthesized plain-language EFCG rationale.
- `created_at`, `updated_at` (DATETIME).

### 8. `holidays`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `name` (VARCHAR(100)): Holiday title (e.g. Thanksgiving).
- `date` (DATE, INDEX): Statutory calendar date.
- `country_code` (VARCHAR(10)): Jurisdiction code.
- `is_mandatory` (INTEGER): Mandatory closure flag.

### 9. `expense_policies`
- `id` (VARCHAR(50), PK): Expense policy ID (e.g. `POL-EXP-TRAVEL`).
- `category` (ENUM, UNIQUE): `TRAVEL`, `MEALS`, `LODGING`, `EQUIPMENT`, `SOFTWARE`, `OFFICE_SUPPLIES`, `OTHER`.
- `max_per_claim` (DECIMAL(10,2)): Maximum monetary value per single claim.
- `daily_limit` (DECIMAL(10,2)): Maximum allowable per diem.
- `receipt_required_above` (DECIMAL(10,2)): Dollar threshold triggering receipt attachment requirement.
- `currency` (VARCHAR(10)): Operating currency.
- `description` (TEXT): Policy terms.

### 10. `expense_claims`
- `id` (VARCHAR(50), PK): Claim ID (e.g. `EXP-2026-000001`).
- `employee_id` (VARCHAR(50), FK -> `employees.id`, INDEX)
- `cost_center_id` (VARCHAR(50), FK -> `cost_centers.id`, INDEX)
- `category` (ENUM): Primary category classification.
- `merchant` (VARCHAR(150)): Vendor or merchant name.
- `claim_date` (DATE, INDEX): Date invoice was incurred.
- `total_amount` (DECIMAL(10,2)): Total monetary amount.
- `currency` (VARCHAR(10)): Currency code.
- `description` (TEXT): Business justification.
- `receipt_url` (VARCHAR(255)): Uploaded receipt storage location.
- `receipt_hash` (VARCHAR(64), INDEX): SHA-256 digital fingerprint of receipt.
- `status` (ENUM): `SUBMITTED`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `CANCELLED`, `REIMBURSED`.
- `decision_state` (ENUM): `ELIGIBLE`, `NEEDS_REVIEW`, `BLOCKED`.
- `decision_explanation` (TEXT): Synthesized plain-language EFCG rationale.
- `created_at`, `updated_at` (DATETIME).

### 11. `expense_lines`
- `id` (VARCHAR(60), PK): Line ID (e.g. `EXPL-EXP-2026-000001-01`).
- `claim_id` (VARCHAR(50), FK -> `expense_claims.id`, INDEX)
- `line_number` (INTEGER): Line item sequence.
- `category` (ENUM): Line category.
- `description` (VARCHAR(255)): Line item detail.
- `amount` (DECIMAL(10,2)): Line monetary amount.
- `receipt_hash` (VARCHAR(64)): Line-level receipt SHA-256 fingerprint.

### 12. `approval_rules`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `request_type` (VARCHAR(20)): `LEAVE` or `EXPENSE`.
- `min_amount` (DECIMAL(10,2)): Threshold floor.
- `max_amount` (DECIMAL(10,2)): Threshold ceiling.
- `required_role` (ENUM): Role authorized to review.
- `step_order` (INTEGER): Stage in sequence.
- `description` (VARCHAR(255)): Rule justification.

### 13. `approval_steps`
- `id` (VARCHAR(80), PK): Step ID (e.g. `APR-EXP-2026-000001-01`).
- `request_id` (VARCHAR(50), INDEX): Associated Leave or Expense ID.
- `request_type` (VARCHAR(20)): `LEAVE` or `EXPENSE`.
- `approver_id` (VARCHAR(50), FK -> `employees.id`, INDEX): Assigned reviewer.
- `step_order` (INTEGER): Order in multi-level approval pipeline.
- `status` (ENUM): `PENDING`, `APPROVED`, `REJECTED`, `INFO_REQUESTED`.
- `comments` (TEXT): Reviewer remarks or mandatory rejection reason.
- `action_timestamp` (DATETIME): Exact action execution timestamp.
- `created_at` (DATETIME): Step generation timestamp.

### 14. `reimbursements`
- `id` (VARCHAR(50), PK): Reimbursement ID (e.g. `RMB-2026-000001`).
- `claim_id` (VARCHAR(50), FK -> `expense_claims.id`, UNIQUE, INDEX)
- `amount` (DECIMAL(10,2)): Disbursed monetary amount.
- `currency` (VARCHAR(10)): Currency code.
- `status` (ENUM): `PENDING`, `PROCESSED`.
- `transaction_ref` (VARCHAR(100)): Banking ACH settlement transaction number.
- `processed_at` (DATETIME): Payout completion timestamp.
- `created_at` (DATETIME).

### 15. `resource_reservations`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `request_id` (VARCHAR(50), INDEX): Linked request ID.
- `resource_type` (ENUM): `LEAVE_DAYS` or `BUDGET_AMOUNT`.
- `employee_id` (VARCHAR(50), FK -> `employees.id`)
- `cost_center_id` (VARCHAR(50), FK -> `cost_centers.id`, NULL)
- `leave_policy_id` (VARCHAR(50), FK -> `leave_policies.id`, NULL)
- `reserved_amount` (DECIMAL(12,2)): Held quota or dollars.
- `previous_available` (DECIMAL(12,2)): Available balance before reservation.
- `final_committed` (DECIMAL(12,2)): Amount converted to permanent spend on approval.
- `status` (ENUM): `RESERVED`, `COMMITTED`, `RELEASED`.
- `created_at`, `updated_at` (DATETIME).

### 16. `audit_events`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `entity_type` (VARCHAR(50), INDEX): e.g. `LEAVE_REQUEST`, `EXPENSE_CLAIM`, `APPROVAL_STEP`.
- `entity_id` (VARCHAR(50), INDEX): Target entity ID.
- `action` (VARCHAR(50)): Operational action (`SUBMITTED`, `STEP_APPROVED`, `CANCELLED`).
- `actor_id` (VARCHAR(50)): Employee ID or `SYSTEM`.
- `previous_hash` (VARCHAR(64)): Predecessor block SHA-256 hash.
- `current_hash` (VARCHAR(64), UNIQUE, INDEX): Block SHA-256 cryptographic signature.
- `payload_json` (TEXT): Canonical JSON event payload.
- `timestamp` (DATETIME, INDEX): UTC creation timestamp.

### 17. `constraint_evaluations`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `request_id` (VARCHAR(50), INDEX): Associated request.
- `request_type` (VARCHAR(20)): `LEAVE` or `EXPENSE`.
- `constraint_name` (VARCHAR(100)): Specific node title.
- `result` (ENUM): `PASS`, `FAIL`, `REVIEW`.
- `actual_value` (TEXT): Real observed condition.
- `expected_value` (TEXT): Required policy threshold.
- `evidence_source` (VARCHAR(100)): Origin of proof (e.g. `Calendar Store`, `Ledger`).
- `evidence_summary` (TEXT): Human-readable evaluation outcome.
- `executed_at` (DATETIME, INDEX).

### 18. `anomaly_alerts`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `anomaly_type` (VARCHAR(100), INDEX): One of 12 classifications.
- `request_id` (VARCHAR(50), INDEX, NULL): Flagged request ID.
- `employee_id` (VARCHAR(50), FK -> `employees.id`, INDEX, NULL): Subject employee.
- `severity` (ENUM): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `detection_method` (VARCHAR(100)): Algorithm used.
- `evidence_json` (TEXT): Supporting metadata.
- `explanation` (TEXT): Case narrative.
- `suggested_action` (TEXT): Actionable remediation instructions.
- `status` (ENUM): `OPEN`, `UNDER_REVIEW`, `CONFIRMED`, `DISMISSED`, `RESOLVED`.
- `resolved_by` (VARCHAR(50), NULL): Reviewer ID.
- `created_at`, `updated_at` (DATETIME).

### 19. `rule_versions`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `rule_type` (VARCHAR(50)): `LEAVE_POLICY` or `EXPENSE_POLICY`.
- `version_number` (INTEGER): Sequential increment.
- `configuration_json` (TEXT): Delta and active parameter specification.
- `effective_date` (DATETIME): Activation timestamp.
- `created_by` (VARCHAR(50)): Process Owner employee ID.
- `description` (TEXT): Revision comments.

### 20. `notifications`
- `id` (INTEGER, PK, AUTOINCREMENT)
- `recipient_id` (VARCHAR(50), FK -> `employees.id`, INDEX): Target user.
- `title` (VARCHAR(150)): Alert heading.
- `message` (TEXT): Body text.
- `category` (VARCHAR(50)): `APPROVAL_PENDING`, `REQUEST_APPROVED`, `INFO_REQUESTED`.
- `is_read` (INTEGER): 0 (Unread) or 1 (Read).
- `link_url` (VARCHAR(255), NULL): In-app deep link.
- `created_at` (DATETIME, INDEX).
