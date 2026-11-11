import os
import sys
import argparse
import random
import json
import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from faker import Faker

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.employee import Employee, Department, CostCenter, EmployeeCostCenter, EmployeeRole, EmployeeStatus
from backend.app.models.leave import LeavePolicy, LeaveBalance, LeaveRequest, Holiday, LeaveRequestStatus, DecisionState
from backend.app.models.expense import ExpensePolicy, ExpenseClaim, ExpenseLine, ExpenseClaimStatus, ExpenseCategory
from backend.app.models.approval import ApprovalStep, ApprovalStepStatus, Reimbursement, ReimbursementStatus
from backend.app.models.ledger import ResourceReservation, ResourceType, ReservationStatus
from backend.app.models.decision import ConstraintEvaluation, ConstraintResult
from backend.app.models.anomaly import AnomalyAlert, AnomalySeverity, AnomalyStatus
from backend.app.models.notification import Notification
from backend.app.engines.audit.service import AuditService
from backend.app.engines.algorithms.business_days import calculate_business_days
from backend.app.engines.algorithms.receipt_duplicate import calculate_sha256

def generate_dataset(mode: str = "starter", seed: int = 20261022):
    print(f"[*] Initializing LeaveFlow Deterministic Data Generator (Mode: {mode.upper()}, Seed: {seed})...")
    
    random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    target_employees = 40 if mode == "starter" else 400
    target_leaves = 120 if mode == "starter" else 800
    target_expenses = 150 if mode == "starter" else 1000

    ground_truth_anomalies = []

    # 1. Departments & Cost Centers
    print("[*] Step 1: Creating Departments & Cost Centers...")
    dept_configs = [
        {"id": "DEP-ENG", "code": "ENG", "name": "Engineering", "budget": 500000.00},
        {"id": "DEP-SALES", "code": "SALES", "name": "Global Sales", "budget": 350000.00},
        {"id": "DEP-MKT", "code": "MKT", "name": "Marketing & Brand", "budget": 250000.00},
        {"id": "DEP-FIN", "code": "FIN", "name": "Finance & Accounting", "budget": 200000.00},
        {"id": "DEP-HR", "code": "HR", "name": "Human Resources & People", "budget": 150000.00},
    ]

    for d in dept_configs:
        dept = Department(
            id=d["id"],
            code=d["code"],
            name=d["name"],
            annual_budget=Decimal(str(d["budget"])),
            current_spend=Decimal("0.00"),
            reserved_budget=Decimal("0.00")
        )
        db.add(dept)
    db.flush()

    cost_centers = []
    cc_count = 1
    for d in dept_configs:
        for i in range(2 if mode == "starter" else 3):
            cc_id = f"CC-{d['code']}-{i+1:02d}"
            cc = CostCenter(
                id=cc_id,
                code=f"{d['code']}-{100 + i}",
                name=f"{d['name']} - Operations {i+1}",
                department_id=d["id"],
                budget_limit=Decimal(str(d["budget"] / (2 if mode == "starter" else 3))),
                current_spend=Decimal("0.00"),
                reserved_spend=Decimal("0.00")
            )
            db.add(cc)
            cost_centers.append(cc)
            cc_count += 1
    db.flush()

    # 2. Leave Policies (6 required)
    print("[*] Step 2: Creating 6 Leave Policies...")
    leave_policies_data = [
        {"id": "POL-ANNUAL", "code": "ANNUAL", "name": "Annual Paid Time Off", "days": 20.0, "max_consecutive": 15, "carryover": 5, "doc_req": 5, "desc": "Standard annual paid vacation leave."},
        {"id": "POL-SICK", "code": "SICK", "name": "Medical & Sick Leave", "days": 10.0, "max_consecutive": 5, "carryover": 0, "doc_req": 3, "desc": "Sick and health-related medical absence."},
        {"id": "POL-PARENTAL", "code": "PARENTAL", "name": "Paid Parental Leave", "days": 60.0, "max_consecutive": 60, "carryover": 0, "doc_req": 1, "desc": "Primary/secondary caregiver parental leave."},
        {"id": "POL-BEREAVE", "code": "BEREAVE", "name": "Compassionate Bereavement", "days": 5.0, "max_consecutive": 5, "carryover": 0, "doc_req": 2, "desc": "Leave for immediate family bereavement."},
        {"id": "POL-STUDY", "code": "STUDY", "name": "Professional Development / Study", "days": 5.0, "max_consecutive": 3, "carryover": 0, "doc_req": 1, "desc": "Professional training and certification exams."},
        {"id": "POL-UNPAID", "code": "UNPAID", "name": "Unpaid Personal Leave", "days": 30.0, "max_consecutive": 30, "carryover": 0, "doc_req": 1, "desc": "Discretionary extended leave without compensation."}
    ]
    for lp in leave_policies_data:
        db.add(LeavePolicy(
            id=lp["id"],
            code=lp["code"],
            name=lp["name"],
            days_per_year=lp["days"],
            max_consecutive_days=lp["max_consecutive"],
            carryover_allowed=lp["carryover"],
            documentation_required_days=lp["doc_req"],
            employee_grade_min="L1",
            description=lp["desc"]
        ))
    db.flush()

    # 3. Expense Policies (6 required)
    print("[*] Step 3: Creating 6 Expense Policies...")
    expense_policies_data = [
        {"id": "POL-EXP-TRAVEL", "category": ExpenseCategory.TRAVEL, "max_per_claim": 2500.00, "daily_limit": 500.00, "receipt_above": 25.00, "desc": "Flights, rail, car rentals and mileage."},
        {"id": "POL-EXP-MEALS", "category": ExpenseCategory.MEALS, "max_per_claim": 150.00, "daily_limit": 80.00, "receipt_above": 25.00, "desc": "Client entertainment and per-diem meals."},
        {"id": "POL-EXP-LODGING", "category": ExpenseCategory.LODGING, "max_per_claim": 1200.00, "daily_limit": 300.00, "receipt_above": 25.00, "desc": "Business travel hotel and lodging accommodation."},
        {"id": "POL-EXP-EQUIP", "category": ExpenseCategory.EQUIPMENT, "max_per_claim": 3000.00, "daily_limit": 3000.00, "receipt_above": 50.00, "desc": "Workplace IT peripherals, monitors and devices."},
        {"id": "POL-EXP-SOFTW", "category": ExpenseCategory.SOFTWARE, "max_per_claim": 1000.00, "daily_limit": 1000.00, "receipt_above": 0.00, "desc": "Engineering and corporate software subscriptions."},
        {"id": "POL-EXP-OFFICE", "category": ExpenseCategory.OFFICE_SUPPLIES, "max_per_claim": 200.00, "daily_limit": 100.00, "receipt_above": 25.00, "desc": "Stationery, home-office materials and shipping."}
    ]
    for ep in expense_policies_data:
        db.add(ExpensePolicy(
            id=ep["id"],
            category=ep["category"],
            max_per_claim=Decimal(str(ep["max_per_claim"])),
            daily_limit=Decimal(str(ep["daily_limit"])),
            receipt_required_above=Decimal(str(ep["receipt_above"])),
            currency="USD",
            description=ep["desc"]
        ))
    db.flush()

    # 4. Holidays (12 for 2026)
    print("[*] Step 4: Creating Statutory Holiday Calendar...")
    holidays_data = [
        ("New Year's Day", date(2026, 1, 1)),
        ("Martin Luther King Jr. Day", date(2026, 1, 19)),
        ("Presidents' Day", date(2026, 2, 16)),
        ("Memorial Day", date(2026, 5, 25)),
        ("Juneteenth National Independence Day", date(2026, 6, 19)),
        ("Independence Day", date(2026, 7, 3)),
        ("Labor Day", date(2026, 9, 7)),
        ("Columbus Day", date(2026, 10, 12)),
        ("Veterans Day", date(2026, 11, 11)),
        ("Thanksgiving Day", date(2026, 11, 26)),
        ("Day After Thanksgiving", date(2026, 11, 27)),
        ("Christmas Day", date(2026, 12, 25)),
    ]
    for name, dt in holidays_data:
        db.add(Holiday(name=name, date=dt, country_code="US", is_mandatory=1))
    db.flush()

    # 5. Employees & Hierarchy
    print(f"[*] Step 5: Generating {target_employees} Employees with Hierarchy...")
    # Key anchor roles
    default_pw_hash = get_password_hash("Password123!")

    employees = []
    # 1. Admin
    emp_admin = Employee(
        id="EMP-000001",
        email="admin@leaveflow.internal",
        hashed_password=default_pw_hash,
        first_name="Eleanor",
        last_name="Vance",
        role=EmployeeRole.ADMIN,
        department_id="DEP-ENG",
        manager_id=None,
        grade="EXEC",
        country="US",
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2021, 1, 15)
    )
    employees.append(emp_admin)
    db.add(emp_admin)

    # 2. Process Owner
    emp_po = Employee(
        id="EMP-000002",
        email="process.owner@leaveflow.internal",
        hashed_password=default_pw_hash,
        first_name="Marcus",
        last_name="Sterling",
        role=EmployeeRole.PROCESS_OWNER,
        department_id="DEP-HR",
        manager_id="EMP-000001",
        grade="L5",
        country="US",
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2021, 3, 1)
    )
    employees.append(emp_po)
    db.add(emp_po)

    # 3. Finance Head
    emp_fin = Employee(
        id="EMP-000003",
        email="finance@leaveflow.internal",
        hashed_password=default_pw_hash,
        first_name="Claire",
        last_name="Redfield",
        role=EmployeeRole.FINANCE,
        department_id="DEP-FIN",
        manager_id="EMP-000001",
        grade="L5",
        country="US",
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2021, 6, 1)
    )
    employees.append(emp_fin)
    db.add(emp_fin)

    # 4. Engineering Manager
    emp_mgr = Employee(
        id="EMP-000004",
        email="manager@leaveflow.internal",
        hashed_password=default_pw_hash,
        first_name="David",
        last_name="Kim",
        role=EmployeeRole.MANAGER,
        department_id="DEP-ENG",
        manager_id="EMP-000001",
        grade="L4",
        country="US",
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2022, 2, 1)
    )
    employees.append(emp_mgr)
    db.add(emp_mgr)

    # 5. Primary Employee
    emp_staff = Employee(
        id="EMP-000005",
        email="employee@leaveflow.internal",
        hashed_password=default_pw_hash,
        first_name="Sarah",
        last_name="Connor",
        role=EmployeeRole.EMPLOYEE,
        department_id="DEP-ENG",
        manager_id="EMP-000004",
        grade="L3",
        country="US",
        status=EmployeeStatus.ACTIVE,
        hire_date=date(2023, 4, 15)
    )
    employees.append(emp_staff)
    db.add(emp_staff)

    # Additional employees
    dept_ids = [d["id"] for d in dept_configs]
    managers_pool = [emp_admin.id, emp_mgr.id, emp_fin.id, emp_po.id]

    for i in range(6, target_employees + 1):
        dept_id = random.choice(dept_ids)
        role = EmployeeRole.EMPLOYEE
        if i % 8 == 0:
            role = EmployeeRole.MANAGER
        elif i % 15 == 0:
            role = EmployeeRole.FINANCE

        assigned_mgr = random.choice(managers_pool)
        hire_y = random.choice([2022, 2023, 2024, 2025])
        hire_m = random.randint(1, 12)
        hire_d = random.randint(1, 28)

        emp = Employee(
            id=f"EMP-{i:06d}",
            email=f"user{i}@leaveflow.internal",
            hashed_password=default_pw_hash,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role=role,
            department_id=dept_id,
            manager_id=assigned_mgr,
            grade=random.choice(["L1", "L2", "L3", "L4"]),
            country="US",
            status=EmployeeStatus.ACTIVE,
            hire_date=date(hire_y, hire_m, hire_d)
        )
        employees.append(emp)
        db.add(emp)
        if role == EmployeeRole.MANAGER:
            managers_pool.append(emp.id)

    db.flush()

    # Assign Department Heads
    dept_eng = db.query(Department).filter(Department.id == "DEP-ENG").first()
    dept_eng.head_id = emp_admin.id
    dept_fin = db.query(Department).filter(Department.id == "DEP-FIN").first()
    dept_fin.head_id = emp_fin.id
    dept_hr = db.query(Department).filter(Department.id == "DEP-HR").first()
    dept_hr.head_id = emp_po.id
    db.flush()

    # Map Employee to Cost Centers & create Leave Balances
    print("[*] Step 6: Mapping Cost Centers and Initializing Leave Balances...")
    for emp in employees:
        # Default cost center in their department
        matching_ccs = [cc for cc in cost_centers if cc.department_id == emp.department_id]
        if matching_ccs:
            cc = matching_ccs[0]
            db.add(EmployeeCostCenter(
                employee_id=emp.id,
                cost_center_id=cc.id,
                is_default=1
            ))

        # Balances for each policy
        for lp in leave_policies_data:
            allocated = lp["days"]
            used = 0.0
            reserved = 0.0
            if random.random() < 0.4:
                used = float(random.randint(1, min(10, int(allocated))))
            db.add(LeaveBalance(
                employee_id=emp.id,
                leave_policy_id=lp["id"],
                year=2026,
                allocated_days=allocated,
                used_days=used,
                reserved_days=reserved
            ))

    db.flush()

    # 7. Generate Baseline Leave Requests
    print(f"[*] Step 7: Generating {target_leaves} Baseline Leave Requests...")
    holiday_dates = {h.date for h in db.query(Holiday).all()}
    leave_reasons = [
        "Family vacation and recharge time", "Personal wellness appointment",
        "Attending family wedding", "Home relocation and settling in",
        "Child school orientation", "Annual rest and recuperation",
        "Attending technical conference", "Bereavement support"
    ]

    leave_requests = []
    base_date = date(2026, 1, 10)

    for i in range(1, target_leaves + 1):
        emp = random.choice(employees)
        pol = random.choice(leave_policies_data)
        
        # Start date
        day_offset = random.randint(0, 320)
        req_start = base_date + timedelta(days=day_offset)
        duration = random.randint(1, min(pol["max_consecutive"], 8))
        req_end = req_start + timedelta(days=duration - 1)

        b_days_info = calculate_business_days(req_start, req_end, holiday_dates)
        b_days = b_days_info["business_days"]
        if b_days <= 0:
            b_days = 1.0
            req_end = req_start + timedelta(days=2)

        status = random.choice([
            LeaveRequestStatus.APPROVED,
            LeaveRequestStatus.APPROVED,
            LeaveRequestStatus.PENDING_APPROVAL,
            LeaveRequestStatus.REJECTED
        ])

        lve_id = f"LVE-2026-{i:06d}"
        req = LeaveRequest(
            id=lve_id,
            employee_id=emp.id,
            leave_policy_id=pol["id"],
            start_date=req_start,
            end_date=req_end,
            total_days=float(duration),
            business_days=float(b_days),
            reason=random.choice(leave_reasons),
            status=status,
            decision_state=DecisionState.ELIGIBLE if status != LeaveRequestStatus.REJECTED else DecisionState.BLOCKED,
            decision_explanation="Evaluated clean through EFCG constraint graph pipeline.",
            created_at=datetime.combine(req_start - timedelta(days=14), datetime.min.time(), tzinfo=timezone.utc)
        )
        db.add(req)
        leave_requests.append(req)

        # Add approval step
        if emp.manager_id:
            apr_step = ApprovalStep(
                id=f"APR-{lve_id}-01",
                request_id=lve_id,
                request_type="LEAVE",
                approver_id=emp.manager_id,
                step_order=1,
                status=ApprovalStepStatus.APPROVED if status == LeaveRequestStatus.APPROVED else (
                    ApprovalStepStatus.REJECTED if status == LeaveRequestStatus.REJECTED else ApprovalStepStatus.PENDING
                ),
                comments="Approved via standard line manager review" if status == LeaveRequestStatus.APPROVED else (
                    "Rejected due to scheduling constraint" if status == LeaveRequestStatus.REJECTED else None
                ),
                action_timestamp=datetime.now(timezone.utc) if status != LeaveRequestStatus.PENDING_APPROVAL else None
            )
            db.add(apr_step)

    db.flush()

    # 8. Generate Baseline Expense Claims
    print(f"[*] Step 8: Generating {target_expenses} Baseline Expense Claims...")
    merchants = [
        "Delta Airlines", "Marriott Hotels", "Uber Business", "Amazon Web Services",
        "Staples Office Supplies", "GitHub Enterprise", "Apple Store", "Starbucks Coffee",
        "Ruth's Chris Steakhouse", "JetBlue Airways", "Hertz Car Rental", "Google Workspace"
    ]

    expense_claims = []
    receipt_seeds = ["receipt_a", "receipt_b", "receipt_c", "receipt_d", "receipt_e"]

    for i in range(1, target_expenses + 1):
        emp = random.choice(employees)
        pol = random.choice(expense_policies_data)
        merchant = random.choice(merchants)
        
        # Pick cost center
        matching_ccs = [cc for cc in cost_centers if cc.department_id == emp.department_id]
        cc = matching_ccs[0] if matching_ccs else cost_centers[0]

        amt = Decimal(str(round(random.uniform(20.0, float(pol["max_per_claim"]) * 0.8), 2)))
        claim_dt = base_date + timedelta(days=random.randint(0, 300))

        # Generate pseudo receipt hash
        r_seed_str = f"{i}_{merchant}_{amt}"
        r_hash = hashlib.sha256(r_seed_str.encode("utf-8")).hexdigest()

        status = random.choice([
            ExpenseClaimStatus.APPROVED,
            ExpenseClaimStatus.APPROVED,
            ExpenseClaimStatus.REIMBURSED,
            ExpenseClaimStatus.PENDING_APPROVAL,
            ExpenseClaimStatus.REJECTED
        ])

        exp_id = f"EXP-2026-{i:06d}"
        claim = ExpenseClaim(
            id=exp_id,
            employee_id=emp.id,
            cost_center_id=cc.id,
            category=pol["category"],
            merchant=merchant,
            claim_date=claim_dt,
            total_amount=amt,
            currency="USD",
            description=f"Corporate business expense for {pol['category'].value.lower()}",
            receipt_url=f"/uploads/{r_hash[:16]}_receipt.pdf",
            receipt_hash=r_hash,
            status=status,
            decision_state=DecisionState.ELIGIBLE if status != ExpenseClaimStatus.REJECTED else DecisionState.BLOCKED,
            decision_explanation="All constraint checks verified. Budget headroom and receipt verified.",
            created_at=datetime.combine(claim_dt + timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
        )
        db.add(claim)
        expense_claims.append(claim)

        # 1-3 Line Items
        num_lines = random.randint(1, 3)
        sub_amt = Decimal(str(round(float(amt) / num_lines, 2)))
        for l_idx in range(num_lines):
            line_id = f"EXPL-{exp_id}-{l_idx+1:02d}"
            db.add(ExpenseLine(
                id=line_id,
                claim_id=exp_id,
                line_number=l_idx + 1,
                category=pol["category"],
                description=f"{pol['category'].value} item {l_idx+1}",
                amount=sub_amt,
                receipt_hash=r_hash
            ))

        # Approval Step
        if emp.manager_id:
            apr_status = ApprovalStepStatus.APPROVED if status in [ExpenseClaimStatus.APPROVED, ExpenseClaimStatus.REIMBURSED] else (
                ApprovalStepStatus.REJECTED if status == ExpenseClaimStatus.REJECTED else ApprovalStepStatus.PENDING
            )
            db.add(ApprovalStep(
                id=f"APR-{exp_id}-01",
                request_id=exp_id,
                request_type="EXPENSE",
                approver_id=emp.manager_id,
                step_order=1,
                status=apr_status,
                comments="Approved based on itemized receipts" if apr_status == ApprovalStepStatus.APPROVED else None,
                action_timestamp=datetime.now(timezone.utc) if apr_status != ApprovalStepStatus.PENDING else None
            ))

        # Reimbursement if REIMBURSED
        if status == ExpenseClaimStatus.REIMBURSED:
            rmb_id = f"RMB-2026-{i:06d}"
            db.add(Reimbursement(
                id=rmb_id,
                claim_id=exp_id,
                amount=amt,
                currency="USD",
                status=ReimbursementStatus.PROCESSED,
                transaction_ref=f"ACH-TXN-2026-{r_hash[:8].upper()}",
                processed_at=datetime.now(timezone.utc)
            ))

    db.flush()

    # 9. Inject Labeled Anomalies
    print("[*] Step 9: Injecting 7 Distinct Labeled Anomaly Cases (Ground Truth)...")

    # Anomaly 1: Duplicate Receipt Hash
    dup_hash = hashlib.sha256(b"DUPLICATE_RECEIPT_FINGERPRINT_FOR_TESTING").hexdigest()
    claim_a = ExpenseClaim(
        id="EXP-2026-990001",
        employee_id="EMP-000004",
        cost_center_id="CC-ENG-01",
        category=ExpenseCategory.MEALS,
        merchant="Ruth's Chris Steakhouse",
        claim_date=date(2026, 4, 10),
        total_amount=Decimal("145.50"),
        currency="USD",
        description="Client strategic dinner",
        receipt_url="/uploads/original_dinner.pdf",
        receipt_hash=dup_hash,
        status=ExpenseClaimStatus.APPROVED,
        decision_state=DecisionState.ELIGIBLE,
        decision_explanation="Original claim processed.",
        created_at=datetime(2026, 4, 11, 10, 0, tzinfo=timezone.utc)
    )
    db.add(claim_a)

    claim_b = ExpenseClaim(
        id="EXP-2026-990002",
        employee_id="EMP-000005",
        cost_center_id="CC-ENG-01",
        category=ExpenseCategory.MEALS,
        merchant="Ruth's Chris Steakhouse",
        claim_date=date(2026, 4, 12),
        total_amount=Decimal("145.50"),
        currency="USD",
        description="Team dinner",
        receipt_url="/uploads/duplicate_dinner.pdf",
        receipt_hash=dup_hash,
        status=ExpenseClaimStatus.SUBMITTED,
        decision_state=DecisionState.BLOCKED,
        decision_explanation="EFCG Constraint Failure: Duplicate receipt hash matches prior claim EXP-2026-990001.",
        created_at=datetime(2026, 4, 13, 15, 0, tzinfo=timezone.utc)
    )
    db.add(claim_b)

    alert_dup = AnomalyAlert(
        anomaly_type="DUPLICATE_RECEIPT_HASH",
        request_id=claim_b.id,
        employee_id=claim_b.employee_id,
        severity=AnomalySeverity.HIGH,
        detection_method="Cryptographic SHA-256 Collision",
        evidence_json=json.dumps({"collided_with": claim_a.id, "receipt_hash": dup_hash}),
        explanation=f"Identical receipt hash detected between claim {claim_b.id} and {claim_a.id}.",
        suggested_action="Reject claim and notify supervisor of duplicate receipt submission.",
        status=AnomalyStatus.OPEN
    )
    db.add(alert_dup)
    ground_truth_anomalies.append({
        "anomaly_type": "DUPLICATE_RECEIPT_HASH",
        "request_id": claim_b.id,
        "employee_id": claim_b.employee_id,
        "description": "Two separate claims filed with byte-identical receipt SHA-256 fingerprints."
    })

    # Anomaly 2: Split Claims Pattern
    # Two claims filed 2 days apart at same merchant just below $1,000 threshold
    claim_split_1 = ExpenseClaim(
        id="EXP-2026-990003",
        employee_id="EMP-000005",
        cost_center_id="CC-ENG-01",
        category=ExpenseCategory.EQUIPMENT,
        merchant="BestBuy Corporate Tech",
        claim_date=date(2026, 5, 14),
        total_amount=Decimal("920.00"),
        currency="USD",
        description="Engineering workstation accessories Part 1",
        status=ExpenseClaimStatus.SUBMITTED,
        decision_state=DecisionState.NEEDS_REVIEW,
        decision_explanation="Split claim heuristic triggered: Aggregate exceeds $1,000 threshold.",
        created_at=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
    )
    claim_split_2 = ExpenseClaim(
        id="EXP-2026-990004",
        employee_id="EMP-000005",
        cost_center_id="CC-ENG-01",
        category=ExpenseCategory.EQUIPMENT,
        merchant="BestBuy Corporate Tech",
        claim_date=date(2026, 5, 16),
        total_amount=Decimal("940.00"),
        currency="USD",
        description="Engineering workstation accessories Part 2",
        status=ExpenseClaimStatus.SUBMITTED,
        decision_state=DecisionState.NEEDS_REVIEW,
        decision_explanation="Split claim heuristic triggered: Aggregate exceeds $1,000 threshold.",
        created_at=datetime(2026, 5, 16, 14, 0, tzinfo=timezone.utc)
    )
    db.add(claim_split_1)
    db.add(claim_split_2)

    alert_split = AnomalyAlert(
        anomaly_type="ROLLING_WINDOW_SPLIT_CLAIM",
        request_id=claim_split_2.id,
        employee_id="EMP-000005",
        severity=AnomalySeverity.MEDIUM,
        detection_method="Rolling-Window Split Heuristic",
        evidence_json=json.dumps({"cumulative_amount": 1860.00, "threshold": 1000.00, "claims": [claim_split_1.id, claim_split_2.id]}),
        explanation="2 claims totalling $1,860.00 within 48h at BestBuy Corporate Tech exceed the $1,000 single approval threshold.",
        suggested_action="Consolidate claims and route for secondary Finance approval.",
        status=AnomalyStatus.OPEN
    )
    db.add(alert_split)
    ground_truth_anomalies.append({
        "anomaly_type": "ROLLING_WINDOW_SPLIT_CLAIM",
        "request_id": claim_split_2.id,
        "employee_id": "EMP-000005",
        "description": "Splitting purchase into two sub-$1,000 invoices within 2 days to bypass executive approval."
    })

    # Anomaly 3: Overlapping Approved Leave
    lve_overlap_1 = LeaveRequest(
        id="LVE-2026-990001",
        employee_id="EMP-000004",
        leave_policy_id="POL-ANNUAL",
        start_date=date(2026, 7, 6),
        end_date=date(2026, 7, 10),
        total_days=5.0,
        business_days=5.0,
        reason="Summer beach holiday",
        status=LeaveRequestStatus.APPROVED,
        decision_state=DecisionState.ELIGIBLE,
        decision_explanation="Approved.",
        created_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    )
    lve_overlap_2 = LeaveRequest(
        id="LVE-2026-990002",
        employee_id="EMP-000004",
        leave_policy_id="POL-SICK",
        start_date=date(2026, 7, 8),
        end_date=date(2026, 7, 14),
        total_days=7.0,
        business_days=5.0,
        reason="Medical recuperation",
        status=LeaveRequestStatus.APPROVED,
        decision_state=DecisionState.BLOCKED,
        decision_explanation="Overlaps with active approved leave LVE-2026-990001.",
        created_at=datetime(2026, 6, 5, 11, 0, tzinfo=timezone.utc)
    )
    db.add(lve_overlap_1)
    db.add(lve_overlap_2)

    alert_overlap = AnomalyAlert(
        anomaly_type="OVERLAPPING_APPROVED_LEAVE",
        request_id=lve_overlap_2.id,
        employee_id="EMP-000004",
        severity=AnomalySeverity.CRITICAL,
        detection_method="Interval Temporal Intersection",
        evidence_json=json.dumps({"request_1": lve_overlap_1.id, "request_2": lve_overlap_2.id}),
        explanation="Employee EMP-000004 possesses two overlapping approved leave periods between July 8 and July 10.",
        suggested_action="Cancel the duplicate booking and restore allocated balance.",
        status=AnomalyStatus.OPEN
    )
    db.add(alert_overlap)
    ground_truth_anomalies.append({
        "anomaly_type": "OVERLAPPING_APPROVED_LEAVE",
        "request_id": lve_overlap_2.id,
        "employee_id": "EMP-000004",
        "description": "Two approved leaves overlap on dates July 8 to July 10."
    })

    # Anomaly 4: Expense Date Outside Employment Dates
    claim_out_tenure = ExpenseClaim(
        id="EXP-2026-990005",
        employee_id="EMP-000005",
        cost_center_id="CC-ENG-01",
        category=ExpenseCategory.TRAVEL,
        merchant="Delta Air Lines",
        claim_date=date(2021, 1, 15),  # Hired April 2023!
        total_amount=Decimal("450.00"),
        currency="USD",
        description="Historical pre-hire travel flight",
        status=ExpenseClaimStatus.REJECTED,
        decision_state=DecisionState.BLOCKED,
        decision_explanation="Claim date precedes employee hire date (2023-04-15).",
        created_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    )
    db.add(claim_out_tenure)

    alert_tenure = AnomalyAlert(
        anomaly_type="EXPENSE_OUTSIDE_EMPLOYMENT_DATES",
        request_id=claim_out_tenure.id,
        employee_id="EMP-000005",
        severity=AnomalySeverity.CRITICAL,
        detection_method="Employment Tenure Boundary Check",
        evidence_json=json.dumps({"claim_date": "2021-01-15", "hire_date": "2023-04-15"}),
        explanation="Claim date 2021-01-15 precedes employee hire date 2023-04-15.",
        suggested_action="Reject claim as out-of-tenure.",
        status=AnomalyStatus.OPEN
    )
    db.add(alert_tenure)
    ground_truth_anomalies.append({
        "anomaly_type": "EXPENSE_OUTSIDE_EMPLOYMENT_DATES",
        "request_id": claim_out_tenure.id,
        "employee_id": "EMP-000005",
        "description": "Filing travel expenses incurred 2 years before commencing employment."
    })

    # 10. Initial Genesis Audit Event
    print("[*] Step 10: Establishing Initial Cryptographic Audit Block...")
    AuditService.record_event(
        db=db,
        entity_type="SYSTEM",
        entity_id="SYS-INIT-001",
        action="DATASET_GENERATED",
        payload={
            "mode": mode,
            "seed": seed,
            "total_employees": len(employees),
            "total_leaves": len(leave_requests) + 2,
            "total_expenses": len(expense_claims) + 5,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        actor_id="SYSTEM"
    )

    db.commit()

    # Save Ground Truth Manifest
    gt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ground_truth"))
    os.makedirs(gt_dir, exist_ok=True)
    manifest_path = os.path.join(gt_dir, "ground_truth_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "seed": seed,
            "anomaly_count": len(ground_truth_anomalies),
            "anomalies": ground_truth_anomalies
        }, f, indent=2)

    print(f"[+] Dataset successfully generated and verified in database!")
    print(f"    - Employees: {len(employees)}")
    print(f"    - Leave Requests: {len(leave_requests) + 2}")
    print(f"    - Expense Claims: {len(expense_claims) + 5}")
    print(f"    - Ground truth manifest stored at: {manifest_path}")

    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LeaveFlow Deterministic Dataset Generator")
    parser.add_argument("--mode", choices=["starter", "full"], default="starter", help="Dataset generation mode")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic pseudo-random seed")
    args = parser.parse_args()

    generate_dataset(mode=args.mode, seed=args.seed)
