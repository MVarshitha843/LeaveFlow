from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.decision import ConstraintResult
from backend.app.models.employee import Employee, CostCenter, EmployeeCostCenter
from backend.app.models.leave import LeavePolicy, LeaveBalance, Holiday
from backend.app.models.expense import ExpensePolicy
from backend.app.engines.constraint_graph.node import ConstraintNode, EvidenceRecord
from backend.app.engines.algorithms.business_days import calculate_business_days
from backend.app.engines.algorithms.interval_overlap import check_interval_overlap
from backend.app.engines.algorithms.split_claim import detect_split_claims
from backend.app.engines.algorithms.receipt_duplicate import check_duplicate_receipt
from backend.app.engines.algorithms.authority_traversal import resolve_approval_chain

def build_leave_constraint_graph(
    db: Session,
    employee_id: str,
    policy_id: str,
    start_date: date,
    end_date: date,
    reason: str,
    document_url: Optional[str] = None,
    current_request_id: Optional[str] = None
) -> List[ConstraintNode]:
    """
    Constructs the directed acyclic graph (DAG) of constraints for a Leave Request.
    """
    nodes: List[ConstraintNode] = []

    # 1. Employee Active Validation
    def eval_emp_active():
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Employee ID {employee_id} not found in database",
                expected_condition="Employee must exist in personnel registry",
                evidence_source="Employee Database",
                reason="Invalid employee identifier"
            )
        if emp.status.value != "ACTIVE":
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Employee status is '{emp.status.value}'",
                expected_condition="Employee status must be 'ACTIVE'",
                evidence_source="Employee Master Record",
                reason=f"Requests cannot be initiated for non-active staff (Status: {emp.status.value})"
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="Employee is ACTIVE",
            expected_condition="Employee must be ACTIVE",
            evidence_source="Employee Master Record",
            reason=f"Active employee verified: {emp.first_name} {emp.last_name} ({emp.grade})",
            details={"hire_date": emp.hire_date.isoformat(), "department_id": emp.department_id}
        )

    nodes.append(ConstraintNode(
        id="NODE_EMP_ACTIVE",
        name="Employee Status Validation",
        description="Verifies the applicant exists and holds an ACTIVE employment status.",
        category="EMPLOYEE",
        is_blocking=True,
        dependencies=[],
        evaluator=eval_emp_active
    ))

    # 2. Employment Date Range Validation
    def eval_employment_dates():
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition="Employee not found",
                expected_condition="Valid employee",
                evidence_source="Employee Record",
                reason="Employee does not exist"
            )
        if start_date < emp.hire_date:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Leave start {start_date} is prior to hire date {emp.hire_date}",
                expected_condition=f"Leave dates must fall on or after hire date ({emp.hire_date})",
                evidence_source="Employment Contract Record",
                reason="Cannot request leave before official date of employment."
            )
        if emp.termination_date and end_date > emp.termination_date:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Leave end {end_date} exceeds termination date {emp.termination_date}",
                expected_condition="Leave dates must not exceed termination date",
                evidence_source="Employment Contract Record",
                reason="Cannot request leave after separation/termination date."
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Requested window ({start_date} to {end_date}) conforms with tenure",
            expected_condition="Dates fall within active employment term",
            evidence_source="Employment Contract Record",
            reason="Leave dates are within active tenure window."
        )

    nodes.append(ConstraintNode(
        id="NODE_EMPLOYMENT_DATES",
        name="Employment Date Conformance",
        description="Ensures the leave request dates fall entirely within active employment tenure.",
        category="EMPLOYEE",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_employment_dates
    ))

    # 3. Policy Conformance & Consecutive Limit
    def eval_policy_conformance():
        policy = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
        if not policy:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Policy '{policy_id}' not found",
                expected_condition="Leave policy must be defined in policy directory",
                evidence_source="Policy Configuration",
                reason="Unrecognized leave policy category."
            )
        calendar_days = (end_date - start_date).days + 1
        if calendar_days > policy.max_consecutive_days:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Requested {calendar_days} calendar days exceeds policy limit of {policy.max_consecutive_days}",
                expected_condition=f"Consecutive leave <= {policy.max_consecutive_days} days",
                evidence_source=f"Policy {policy.name}",
                reason=f"Exceeds maximum consecutive duration threshold for {policy.name}."
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Duration ({calendar_days} days) within consecutive ceiling ({policy.max_consecutive_days} days)",
            expected_condition=f"Consecutive leave <= {policy.max_consecutive_days} days",
            evidence_source=f"Policy {policy.name}",
            reason="Duration complies with consecutive absence regulations."
        )

    nodes.append(ConstraintNode(
        id="NODE_POLICY_ELIGIBILITY",
        name="Policy Duration Conformance",
        description="Checks requested absence against maximum consecutive duration allowances.",
        category="POLICY",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_policy_conformance
    ))

    # 4. Holiday Exclusions & Business Day Calculation
    def eval_working_days():
        holidays = db.query(Holiday).all()
        holiday_dates = {h.date for h in holidays}
        result = calculate_business_days(start_date, end_date, holiday_dates)
        if not result["valid_range"]:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=result["error"] or "Invalid dates",
                expected_condition="Start date <= End date",
                evidence_source="Date Arithmetic",
                reason="Start date cannot follow end date."
            )
        if result["business_days"] == 0:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition="0 business days requested (all dates are weekends/holidays)",
                expected_condition="Leave must contain at least 1 working business day",
                evidence_source="Calendar & Holiday Schedule",
                reason="Selected interval contains zero working business days. Review required.",
                details=result
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Calculated {result['business_days']:.1f} business day(s) (Excluded: {result['weekend_days']} weekend, {result['holiday_days']} holiday)",
            expected_condition="Positive business working day calculation",
            evidence_source="Calendar & Holiday Schedule",
            reason=f"Computed {result['business_days']:.1f} working day(s) successfully.",
            details=result
        )

    nodes.append(ConstraintNode(
        id="NODE_WORKING_DAYS",
        name="Working Day Calculation",
        description="Excludes statutory holidays and weekend days to establish accurate net business days.",
        category="CALENDAR",
        is_blocking=True,
        dependencies=["NODE_EMPLOYMENT_DATES"],
        evaluator=eval_working_days
    ))

    # 5. Leave Balance Availability
    def eval_leave_balance():
        holidays = db.query(Holiday).all()
        holiday_dates = {h.date for h in holidays}
        b_days_info = calculate_business_days(start_date, end_date, holiday_dates)
        b_days = b_days_info["business_days"]

        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_policy_id == policy_id,
            LeaveBalance.year == 2026
        ).first()

        if not balance:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition="No balance ledger account found",
                expected_condition="Active leave balance account",
                evidence_source="Leave Balance Ledger",
                reason="Employee possesses no allocation record for this policy."
            )

        available = balance.allocated_days - balance.used_days - balance.reserved_days
        if available < b_days:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Available balance is {available:.1f} days, requested {b_days:.1f} days",
                expected_condition=f"Available balance >= {b_days:.1f} days",
                evidence_source="Leave Balance Ledger",
                reason=f"Insufficient leave balance (Shortfall: {b_days - available:.1f} days).",
                details={"allocated": balance.allocated_days, "used": balance.used_days, "reserved": balance.reserved_days, "available": available}
            )

        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Available balance {available:.1f} days >= requested {b_days:.1f} days",
            expected_condition=f"Available balance >= {b_days:.1f} days",
            evidence_source="Leave Balance Ledger",
            reason=f"Balance sufficient. Remaining available after reservation will be {available - b_days:.1f} days.",
            details={"allocated": balance.allocated_days, "used": balance.used_days, "reserved": balance.reserved_days, "available": available}
        )

    nodes.append(ConstraintNode(
        id="NODE_BALANCE_CHECK",
        name="Leave Balance Availability",
        description="Verifies unreserved leave balance sufficiency in the reservation ledger.",
        category="FINANCIAL",
        is_blocking=True,
        dependencies=["NODE_POLICY_ELIGIBILITY", "NODE_WORKING_DAYS"],
        evaluator=eval_leave_balance
    ))

    # 6. Interval Overlap Detection
    def eval_overlap():
        res = check_interval_overlap(db, employee_id, start_date, end_date, current_request_id)
        if res["has_overlap"]:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Overlaps with {len(res['conflicts'])} active leave request(s)",
                expected_condition="Zero conflicting approved or pending leave intervals",
                evidence_source="Leave Schedule Store",
                reason=res["message"],
                details=res
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="No overlapping intervals found",
            expected_condition="Zero conflicting approved or pending leave intervals",
            evidence_source="Leave Schedule Store",
            reason="Schedule verification clear of overlapping bookings."
        )

    nodes.append(ConstraintNode(
        id="NODE_OVERLAP_CHECK",
        name="Schedule Overlap Verification",
        description="Ensures employee has no overlapping pending or approved leave bookings.",
        category="CALENDAR",
        is_blocking=True,
        dependencies=["NODE_EMPLOYMENT_DATES"],
        evaluator=eval_overlap
    ))

    # 7. Documentation Verification
    def eval_documentation():
        policy = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
        req_doc = policy.documentation_required_days if policy else 3
        calendar_days = (end_date - start_date).days + 1

        if calendar_days >= req_doc and (not document_url or document_url.strip() == ""):
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Absence is {calendar_days} days without supporting medical/legal documentation",
                expected_condition=f"Documentation recommended for absences >= {req_doc} days",
                evidence_source="Attachment Verification",
                reason="Supporting documentation missing for extended absence. Requires manager discretion.",
                details={"calendar_days": calendar_days, "threshold": req_doc}
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="Documentation requirements fulfilled or not mandated",
            expected_condition="Supporting document when required",
            evidence_source="Attachment Verification",
            reason="Document compliance verified."
        )

    nodes.append(ConstraintNode(
        id="NODE_DOCUMENTATION",
        name="Documentation Compliance",
        description="Verifies whether required certificates or documentation are attached.",
        category="POLICY",
        is_blocking=False,
        dependencies=["NODE_WORKING_DAYS"],
        evaluator=eval_documentation
    ))

    # 8. Authority Hierarchy & Anti-Self-Approval
    def eval_authority():
        try:
            chain = resolve_approval_chain(db, employee_id, "LEAVE", 1.0)
            if not chain:
                return EvidenceRecord(
                    result=ConstraintResult.REVIEW,
                    actual_condition="Approval routing produced zero eligible steps",
                    expected_condition="At least one authorized approver",
                    evidence_source="Authority Graph",
                    reason="No designated approver found. Escalated to Process Owner for manual routing."
                )
            return EvidenceRecord(
                result=ConstraintResult.PASS,
                actual_condition=f"Valid approval chain resolved ({len(chain)} stage(s)). No self-approvals.",
                expected_condition="Valid approval hierarchy without self-approval",
                evidence_source="Authority Graph",
                reason=f"Routing confirmed through: {', '.join(c['approver_name'] for c in chain)}",
                details={"chain": chain}
            )
        except Exception as e:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Authority routing error: {str(e)}",
                expected_condition="Resolvable hierarchy without self-approval",
                evidence_source="Authority Graph",
                reason=str(e)
            )

    nodes.append(ConstraintNode(
        id="NODE_AUTHORITY_CHECK",
        name="Approval Authority Routing",
        description="Traverses reporting hierarchy ensuring valid approvers and zero self-approvals.",
        category="AUTHORITY",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_authority
    ))

    return nodes

def build_expense_constraint_graph(
    db: Session,
    employee_id: str,
    cost_center_id: str,
    category: str,
    merchant: str,
    claim_date: date,
    total_amount: Decimal,
    receipt_url: Optional[str] = None,
    receipt_hash: Optional[str] = None,
    current_claim_id: Optional[str] = None
) -> List[ConstraintNode]:
    """
    Constructs the directed acyclic graph (DAG) of constraints for an Expense Claim.
    """
    nodes: List[ConstraintNode] = []

    # 1. Employee Active Validation
    def eval_emp_active():
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Employee ID {employee_id} not found",
                expected_condition="Active employee in company directory",
                evidence_source="Employee Database",
                reason="Applicant ID does not exist."
            )
        if emp.status.value != "ACTIVE":
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Employee status is '{emp.status.value}'",
                expected_condition="Employee status must be 'ACTIVE'",
                evidence_source="Employee Master Record",
                reason=f"Expenses cannot be claimed by non-active personnel (Status: {emp.status.value})"
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="Employee is ACTIVE",
            expected_condition="Employee must be ACTIVE",
            evidence_source="Employee Master Record",
            reason=f"Active employee verified: {emp.first_name} {emp.last_name}"
        )

    nodes.append(ConstraintNode(
        id="NODE_EMP_ACTIVE",
        name="Employee Status Validation",
        description="Verifies the applicant is an active corporate employee.",
        category="EMPLOYEE",
        is_blocking=True,
        dependencies=[],
        evaluator=eval_emp_active
    ))

    # 2. Employment Dates Conformance
    def eval_employment_dates():
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition="Employee missing",
                expected_condition="Valid employee",
                evidence_source="Employee Master Record",
                reason="Employee does not exist"
            )
        if claim_date < emp.hire_date:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Expense date {claim_date} is prior to hire date {emp.hire_date}",
                expected_condition=f"Expense date must be >= hire date ({emp.hire_date})",
                evidence_source="Employment Contract",
                reason="Expenses incurred prior to employment cannot be reimbursed."
            )
        if emp.termination_date and claim_date > emp.termination_date:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Expense date {claim_date} exceeds termination date {emp.termination_date}",
                expected_condition="Expense date must be <= termination date",
                evidence_source="Employment Contract",
                reason="Expenses incurred following employee departure are ineligible."
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Expense date {claim_date} falls within active tenure",
            expected_condition="Expense incurred during active tenure",
            evidence_source="Employment Contract",
            reason="Date of expense complies with active employment timeline."
        )

    nodes.append(ConstraintNode(
        id="NODE_EMPLOYMENT_DATES",
        name="Employment Date Conformance",
        description="Ensures the expense was incurred during active employment.",
        category="EMPLOYEE",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_employment_dates
    ))

    # 3. Cost Center Assignment Validation
    def eval_cost_center():
        cc = db.query(CostCenter).filter(CostCenter.id == cost_center_id).first()
        if not cc:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Cost Center '{cost_center_id}' not found in registry",
                expected_condition="Cost center must exist and be assigned",
                evidence_source="Financial Cost Center Registry",
                reason="Invalid or missing cost center. Requires Finance assignment before allocation."
            )
        # Check mapping
        mapping = db.query(EmployeeCostCenter).filter(
            EmployeeCostCenter.employee_id == employee_id,
            EmployeeCostCenter.cost_center_id == cost_center_id
        ).first()

        if not mapping:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Employee {employee_id} is not mapped to cost center {cc.code} ({cc.name})",
                expected_condition="Employee assigned to specified cost center",
                evidence_source="Cost Center Allocation Matrix",
                reason="Cost center is outside employee's default department allocations. Marked for Finance confirmation.",
                details={"cost_center_code": cc.code, "cost_center_name": cc.name}
            )

        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Employee mapped to {cc.code} - {cc.name}",
            expected_condition="Valid cost center mapping",
            evidence_source="Cost Center Allocation Matrix",
            reason="Cost center assignment verified."
        )

    nodes.append(ConstraintNode(
        id="NODE_COST_CENTER",
        name="Cost Center Assignment",
        description="Validates cost center existence and employee billing authorization.",
        category="FINANCIAL",
        is_blocking=False,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_cost_center
    ))

    # 4. Expense Policy Limits
    def eval_policy_limits():
        policy = db.query(ExpensePolicy).filter(ExpensePolicy.category == category).first()
        if not policy:
            return EvidenceRecord(
                result=ConstraintResult.PASS,
                actual_condition="General category (no strict cap defined)",
                expected_condition="Conform to standard expense guidelines",
                evidence_source="Policy Handbook",
                reason="General policy guidelines apply."
            )
        if total_amount > policy.max_per_claim:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Amount ${total_amount:,.2f} exceeds ${policy.max_per_claim:,.2f} maximum per-claim limit for {category}",
                expected_condition=f"Claim amount <= ${policy.max_per_claim:,.2f}",
                evidence_source=f"Expense Policy ({category})",
                reason=f"Claim exceeds maximum per-claim allowance for {category}.",
                details={"amount": float(total_amount), "max_per_claim": float(policy.max_per_claim)}
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Amount ${total_amount:,.2f} within limit (${policy.max_per_claim:,.2f})",
            expected_condition=f"Claim amount <= ${policy.max_per_claim:,.2f}",
            evidence_source=f"Expense Policy ({category})",
            reason=f"Amount satisfies per-claim allowance for category {category}."
        )

    nodes.append(ConstraintNode(
        id="NODE_POLICY_LIMIT",
        name="Expense Policy Ceiling",
        description="Verifies the claim amount complies with category-specific per-claim financial caps.",
        category="POLICY",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_policy_limits
    ))

    # 5. Receipt Document Verification
    def eval_receipt_verification():
        policy = db.query(ExpensePolicy).filter(ExpensePolicy.category == category).first()
        receipt_threshold = policy.receipt_required_above if policy else Decimal("25.00")

        if total_amount >= receipt_threshold and (not receipt_url or receipt_url.strip() == ""):
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Claim amount ${total_amount:,.2f} requires itemized receipt (threshold: ${receipt_threshold:,.2f}) but none provided",
                expected_condition="Receipt upload required for claims >= $25.00",
                evidence_source="Document Ingestion",
                reason="Receipt missing. Routed to applicant for additional evidence submission before approval.",
                details={"amount": float(total_amount), "threshold": float(receipt_threshold)}
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="Receipt attached and validated or below threshold",
            expected_condition="Receipt verification satisfied",
            evidence_source="Document Ingestion",
            reason="Receipt requirement satisfied."
        )

    nodes.append(ConstraintNode(
        id="NODE_RECEIPT_VERIFICATION",
        name="Receipt Document Verification",
        description="Checks itemized receipt submission when claims surpass policy thresholds.",
        category="POLICY",
        is_blocking=False,
        dependencies=["NODE_POLICY_LIMIT"],
        evaluator=eval_receipt_verification
    ))

    # 6. Duplicate Receipt Detection via SHA-256
    def eval_duplicate_receipt():
        dup_res = check_duplicate_receipt(db, receipt_hash, current_claim_id)
        if dup_res["has_duplicate"]:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Identical receipt hash matches {len(dup_res['matching_claims'])} prior claim(s)",
                expected_condition="Unique digital receipt fingerprint (SHA-256)",
                evidence_source="Cryptographic Hash Detector",
                reason=dup_res["message"],
                details=dup_res
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="Receipt SHA-256 fingerprint is unique",
            expected_condition="Unique receipt hash across active claims",
            evidence_source="Cryptographic Hash Detector",
            reason="No identical receipts found across historical repository."
        )

    nodes.append(ConstraintNode(
        id="NODE_RECEIPT_DUPLICATE",
        name="Receipt SHA-256 Uniqueness",
        description="Scans repository for duplicate receipts via cryptographic SHA-256 matching.",
        category="FRAUD_CHECK",
        is_blocking=True,
        dependencies=["NODE_RECEIPT_VERIFICATION"],
        evaluator=eval_duplicate_receipt
    ))

    # 7. Rolling-Window Split Claim Detection
    def eval_split_claim():
        split_res = detect_split_claims(
            db=db,
            employee_id=employee_id,
            claim_date=claim_date,
            current_amount=total_amount,
            category=category,
            merchant=merchant,
            cost_center_id=cost_center_id,
            current_claim_id=current_claim_id
        )
        if split_res["is_suspicious_split"]:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Cumulative spend in {split_res['window_days']}-day window is ${split_res['cumulative_amount']:,.2f} (exceeds ${split_res['threshold']:,.2f})",
                expected_condition="Normal transaction frequency without threshold avoidance pattern",
                evidence_source="Rolling-Window Heuristic",
                reason=split_res["explanation"],
                details=split_res
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition="No split claim clustering detected in rolling window",
            expected_condition="Normal transaction grouping",
            evidence_source="Rolling-Window Heuristic",
            reason="No threshold-evasion claim splitting detected."
        )

    nodes.append(ConstraintNode(
        id="NODE_SPLIT_CLAIM",
        name="Split Claim Pattern Heuristic",
        description="Analyzes rolling-window claim frequencies to detect suspicious threshold-avoidance clustering.",
        category="FRAUD_CHECK",
        is_blocking=False,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_split_claim
    ))

    # 8. Department & Cost Center Budget Check
    def eval_budget():
        cc = db.query(CostCenter).filter(CostCenter.id == cost_center_id).first()
        if not cc:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition="Cost center not resolved",
                expected_condition="Active cost center with defined budget",
                evidence_source="Budget Ledger",
                reason="Cannot verify budget availability for unverified cost center."
            )
        available = cc.budget_limit - cc.current_spend - cc.reserved_spend
        if available < total_amount:
            return EvidenceRecord(
                result=ConstraintResult.REVIEW,
                actual_condition=f"Cost center remaining budget is ${available:,.2f}, claim is ${total_amount:,.2f}",
                expected_condition=f"Remaining budget >= ${total_amount:,.2f}",
                evidence_source="Financial Ledger",
                reason=f"Claim exceeds available cost center budget by ${total_amount - available:,.2f}. Finance review required for budget override.",
                details={"budget_limit": float(cc.budget_limit), "current_spend": float(cc.current_spend), "reserved_spend": float(cc.reserved_spend), "available": float(available)}
            )
        return EvidenceRecord(
            result=ConstraintResult.PASS,
            actual_condition=f"Cost center available budget (${available:,.2f}) covers ${total_amount:,.2f}",
            expected_condition=f"Remaining budget >= ${total_amount:,.2f}",
            evidence_source="Financial Ledger",
            reason=f"Budget headroom confirmed. Post-reservation availability will be ${available - total_amount:,.2f}.",
            details={"budget_limit": float(cc.budget_limit), "current_spend": float(cc.current_spend), "reserved_spend": float(cc.reserved_spend), "available": float(available)}
        )

    nodes.append(ConstraintNode(
        id="NODE_BUDGET_CHECK",
        name="Budget Headroom Verification",
        description="Confirms cost center possesses sufficient unreserved budget to cover claim amount.",
        category="FINANCIAL",
        is_blocking=False,
        dependencies=["NODE_COST_CENTER", "NODE_POLICY_LIMIT"],
        evaluator=eval_budget
    ))

    # 9. Authority Routing & Anti-Self-Approval
    def eval_authority():
        try:
            chain = resolve_approval_chain(db, employee_id, "EXPENSE", float(total_amount), category)
            if not chain:
                return EvidenceRecord(
                    result=ConstraintResult.REVIEW,
                    actual_condition="Zero approval steps resolved",
                    expected_condition="At least one authorized approver",
                    evidence_source="Authority Graph",
                    reason="No designated approver found. Escalated to Finance for manual assignment."
                )
            return EvidenceRecord(
                result=ConstraintResult.PASS,
                actual_condition=f"Approval chain resolved ({len(chain)} stage(s)). Self-approval strictly forbidden.",
                expected_condition="Valid approval routing without self-approval",
                evidence_source="Authority Graph",
                reason=f"Routing assigned to: {', '.join(c['approver_name'] for c in chain)}",
                details={"chain": chain}
            )
        except Exception as e:
            return EvidenceRecord(
                result=ConstraintResult.FAIL,
                actual_condition=f"Authority routing error: {str(e)}",
                expected_condition="Resolvable hierarchy without self-approval",
                evidence_source="Authority Graph",
                reason=str(e)
            )

    nodes.append(ConstraintNode(
        id="NODE_AUTHORITY_CHECK",
        name="Approval Authority Routing",
        description="Traverses hierarchy to construct multi-level approval steps with strict anti-self-approval.",
        category="AUTHORITY",
        is_blocking=True,
        dependencies=["NODE_EMP_ACTIVE"],
        evaluator=eval_authority
    ))

    return nodes
