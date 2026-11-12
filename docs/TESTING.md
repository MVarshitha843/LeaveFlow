# Testing and Quality Assurance in LeaveFlow

This document explains how testing is organized in LeaveFlow, how to run the test suite, what each test case verifies, and how we verified the frontend and backend workflows.

Everything documented here reflects the actual test files, commands, and results in the repository.

---

## 1. Testing Philosophy

In enterprise software handling employee leave, payroll reserves, and financial reimbursements, reliability and compliance are critical:
- A leave overdraw can cause payroll discrepancies or staffing shortages.
- A missed duplicate receipt or undetected split expense can lead to financial loss.
- An approval routing error (such as self-approval) violates basic internal audit controls.

Because of this, we designed LeaveFlow's core engine around deterministic algorithms and wrote automated tests to verify:
1. **Mathematical correctness**: Business-day counting, holiday exclusions, and rolling-window sums.
2. **Constraint graph evaluation**: Dependency resolution in the Evidence-First Constraint Graph (EFCG) and 3-state output (`PASS`, `FAIL`, `REVIEW`).
3. **Ledger invariants**: Preventing overdraws, atomic reservation commitments, and release on rejection.
4. **Audit integrity**: Tamper detection in cryptographic SHA-256 hash chains.
5. **End-to-end user workflows**: Complete request lifecycles through HTTP endpoints with role-based authentication.

---

## 2. Environment Setup and Running the Application

Before running tests or verifying the application, ensure your local environment is configured.

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.11.9)
- **Node.js**: 18+ (tested on Node.js v20+)
- **Operating System**: Windows, macOS, or Linux

### Step 1: Backend Setup
From the repository root:

```bash
# Navigate to backend and create a virtual environment (if not already created)
python -m venv backend/venv

# Activate the virtual environment
# Windows (PowerShell):
backend\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
backend\venv\Scripts\activate.bat
# Linux / macOS:
source backend/venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Database Initialization (Synthetic Dataset)
LeaveFlow comes with a seeded SQLite database (`data/leaveflow.db`). If you ever need to re-seed or regenerate fresh ground-truth data:

```bash
# Run the synthetic data generator
python scripts/generate_data.py --mode full
```
This generates 400 employees, company hierarchies, cost centers, leave balances, historical requests, and 7 labeled anomaly scenarios.

### Step 3: Running the Backend Server
```bash
# From repository root
backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Alternatively, on Windows you can double-click `run_backend.bat`.

The API documentation is interactively accessible at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Step 4: Frontend Setup and Running
In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```
Alternatively, on Windows you can double-click `run_frontend.bat`.

The frontend dev server runs at `http://localhost:5173`. Vite is configured with a reverse proxy in `vite.config.ts` so that requests to `/api` and `/uploads` are automatically forwarded to `http://127.0.0.1:8000`.

---

## 3. How to Execute Backend Tests

The automated backend tests are written using **pytest** and **FastAPI TestClient** (built on Starlette / HTTPX).

### Running All Tests
From the repository root with the virtual environment active:

```bash
# Using pytest directly
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

On Windows, you can also run the provided batch script:
```cmd
.\run_tests.bat
```

### Verified Test Run Results
When executed, all 14 tests run and pass in under 0.5 seconds:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: E:\Leaveflow_Assignment
plugins: anyio-4.16.0, Faker-40.54.0
collected 14 items

backend/tests/test_e2e_scenarios.py::test_scenario_a_leave_lifecycle_complete PASSED [  7%]
backend/tests/test_e2e_scenarios.py::test_scenario_b_expense_lifecycle_complete PASSED [ 14%]
backend/tests/test_e2e_scenarios.py::test_scenario_c_split_claims_detected_and_reviewed PASSED [ 21%]
backend/tests/test_e2e_scenarios.py::test_scenario_d_missing_receipt_request_info PASSED [ 28%]
backend/tests/test_efcg_core.py::test_business_days_with_holidays PASSED [ 35%]
backend/tests/test_efcg_core.py::test_interval_overlap_detection PASSED  [ 42%]
backend/tests/test_efcg_core.py::test_split_claim_suspicious_detector PASSED [ 50%]
backend/tests/test_efcg_core.py::test_receipt_duplicate_detection PASSED [ 57%]
backend/tests/test_efcg_core.py::test_authority_graph_zero_self_approval PASSED [ 64%]
backend/tests/test_efcg_core.py::test_efcg_leave_graph_evaluation PASSED [ 71%]
backend/tests/test_ledger_and_audit.py::test_leave_reservation_commit_and_release PASSED [ 78%]
backend/tests/test_ledger_and_audit.py::test_prevent_double_allocation_or_overdraw PASSED [ 85%]
backend/tests/test_ledger_and_audit.py::test_tamper_evident_audit_chain_verification PASSED [ 92%]
backend/tests/test_ledger_and_audit.py::test_audit_chain_tamper_detection PASSED [100%]

======================= 14 passed, 21 warnings in 0.42s =======================
```

---

## 4. Detailed Breakdown of Test Suites

The 14 test cases are organized into 3 files according to their testing layer:

```
backend/tests/
├── test_efcg_core.py        (6 tests: Pure algorithms, constraint evaluations, authority rules)
├── test_ledger_and_audit.py (4 tests: Dual-ledger reservations, overdraw prevention, audit chain)
└── test_e2e_scenarios.py    (4 tests: Full HTTP lifecycles, role permissions, approval workflows)
```

---

### Suite 1: EFCG Core Algorithms (`test_efcg_core.py`)

This suite verifies the core business logic algorithms independently of HTTP routing:

#### 1. `test_business_days_with_holidays`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `backend.app.engines.algorithms.business_days.calculate_business_days`
- **Verification details**:
  - Input: January 15, 2026 (Thursday) to January 21, 2026 (Wednesday) = 7 calendar days.
  - Injected holiday: January 19, 2026 (Martin Luther King Jr. Day).
  - Asserts that weekends (Saturday Jan 17, Sunday Jan 18 = 2 days) and the holiday (1 day) are deducted.
  - Net calculated business days: exactly 4.0 days (Thursday, Friday, Tuesday, Wednesday).
  - Confirms `valid_range == True` and `len(excluded_dates) == 3`.

#### 2. `test_interval_overlap_detection`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `backend.app.engines.algorithms.interval_overlap.check_interval_overlap`
- **Verification details**:
  - Uses seeded employee `EMP-000004` who has an existing approved leave from July 6 to July 10, 2026.
  - Case A (Conflict): Submits a date range from July 7 to July 9, 2026. Asserts `has_overlap == True` and conflicts list is non-empty.
  - Case B (Clean): Submits a future non-overlapping range from February 1 to February 5, 2027. Asserts `has_overlap == False`.

#### 3. `test_split_claim_suspicious_detector`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `backend.app.engines.algorithms.split_claim.detect_split_claims`
- **Verification details**:
  - Employee `EMP-000005` has existing expense claims at merchant "BestBuy Corporate Tech" between May 14 and May 16, 2026.
  - Submits a new claim on May 17, 2026 for \$910.00 under category `EQUIPMENT`.
  - With a 7-day rolling window and single-claim threshold of \$1,000, the individual claim appears beneath the threshold, but the cumulative rolling total exceeds \$1,000.
  - Asserts `is_suspicious_split == True`, `pattern_type == "ROLLING_WINDOW_SPLIT_CLAIM"`, and `cumulative_amount > 1000.0`.

#### 4. `test_receipt_duplicate_detection`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `calculate_sha256` and `check_duplicate_receipt`
- **Verification details**:
  - Generates a SHA-256 hash of arbitrary bytes and confirms it produces a valid 64-character hexadecimal digest.
  - Queries the database for a known pre-seeded duplicate hash (`DUPLICATE_RECEIPT_FINGERPRINT_FOR_TESTING`).
  - Asserts `has_duplicate == True` and matching historical claims are identified.

#### 5. `test_authority_graph_zero_self_approval`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `backend.app.engines.algorithms.authority_traversal.resolve_approval_chain`
- **Verification details**:
  - Evaluates approval chain for regular employee `EMP-000005` (Manager is `EMP-000004`). Verifies every step approver is not the employee (`approver_id != "EMP-000005"`).
  - Evaluates approval chain for Department Admin / Executive `EMP-000001` who has no higher manager. Asserts that routing automatically redirects to another authorized officer and never falls back to self-approval.

#### 6. `test_efcg_leave_graph_evaluation`
- **File**: `backend/tests/test_efcg_core.py`
- **What it tests**: `build_leave_constraint_graph` and `DecisionSynthesizer.execute_graph`
- **Verification details**:
  - Builds the 8-node constraint DAG for employee `EMP-000005` applying for 5 days of annual leave.
  - Executes topological graph traversal without persisting to database.
  - Asserts that all nodes are evaluated, `decision_state` is computed (`ELIGIBLE` or `NEEDS_REVIEW`), execution order covers all nodes, and a structured explanation payload is produced.

---

### Suite 2: Ledger and Cryptographic Audit (`test_ledger_and_audit.py`)

This suite verifies financial and leave balance safety invariants and hash-chain audit integrity:

#### 7. `test_leave_reservation_commit_and_release`
- **File**: `backend/tests/test_ledger_and_audit.py`
- **What it tests**: `ResourceReservationLedger.reserve_leave`, `commit_leave`, and `release_leave`
- **Verification details**:
  - Reads initial `reserved_days` and `used_days` for employee `EMP-000005`.
  - **Reserve Phase**: Reserves 3.0 days. Asserts ledger entry status is `RESERVED`, and balance table `reserved_days` increases by exactly 3.0.
  - **Commit Phase**: Commits the reservation. Asserts status is `COMMITTED`, `reserved_days` returns to baseline, and `used_days` increments by 3.0.
  - **Release Phase**: Reserves 2.0 days for a second test request, then cancels it. Calls `release_leave()`. Asserts status is `RELEASED` and `reserved_days` returns cleanly to baseline without affecting `used_days`.

#### 8. `test_prevent_double_allocation_or_overdraw`
- **File**: `backend/tests/test_ledger_and_audit.py`
- **What it tests**: Balance validation guard in `ResourceReservationLedger.reserve_leave`
- **Verification details**:
  - Attempts to reserve 9,999 days of leave for employee `EMP-000005`.
  - Asserts that `pytest.raises(ValueError)` triggers with message `"Insufficient available leave balance"`.
  - Confirms the ledger rejects overdrawn requests before touching database balances.

#### 9. `test_tamper_evident_audit_chain_verification`
- **File**: `backend/tests/test_ledger_and_audit.py`
- **What it tests**: `AuditService.record_event` and `AuditService.verify_integrity`
- **Verification details**:
  - Records an audit event using `AuditService.record_event()` with actor ID, entity details, and JSON payload.
  - Chains the event hash to the previous event's SHA-256 hash.
  - Runs `AuditService.verify_integrity()`. Asserts `is_valid == True` across all recorded events.
  - Cleans up the test record after verification.

#### 10. `test_audit_chain_tamper_detection`
- **File**: `backend/tests/test_ledger_and_audit.py`
- **What it tests**: Detection of unauthorized database modifications
- **Verification details**:
  - Records a legitimate audit event with payload `{"sensitive_budget": 500}`.
  - Simulates an attacker modifying the database directly via SQL: updates `payload_json` to `{"sensitive_budget": 999999}` without recalculating the hash.
  - Runs `AuditService.verify_integrity()`. Asserts `is_valid == False`, `error_type == "PAYLOAD_TAMPERED"`, and pinpointed `corrupted_event_id` matches the mutated record.
  - Deletes the test record to restore the audit chain to a clean state.

---

### Suite 3: End-to-End Scenarios (`test_e2e_scenarios.py`)

This suite runs real HTTP calls using `TestClient` and validates multi-step role-based workflows:

#### 11. `test_scenario_a_leave_lifecycle_complete`
- **File**: `backend/tests/test_e2e_scenarios.py`
- **Workflow**: Employee Submit -> EFCG Evaluation -> Graph Inspection -> Manager Approval -> Balance Commit -> Audit Trail
- **Verification details**:
  - Employee logs in and submits a leave request for 3 business days via `POST /api/leave/requests`.
  - Confirms response returns `decision_state in ["ELIGIBLE", "NEEDS_REVIEW"]` and `status == "PENDING_APPROVAL"`.
  - Calls `GET /api/decision/{request_id}/graph` to verify that the frontend graph endpoint returns all 7+ evaluated nodes.
  - Manager logs in, fetches pending approval steps via `GET /api/approvals/request/{request_id}`, and approves via `POST /api/approvals/{step_id}/approve`.
  - Confirms `final_approval == True`, request status transitions to `APPROVED`, and leave balance is committed.
  - Fetches audit trail via `GET /api/audit/request/{request_id}` and asserts actions `SUBMITTED` and `STEP_APPROVED` are recorded.

#### 12. `test_scenario_b_expense_lifecycle_complete`
- **File**: `backend/tests/test_e2e_scenarios.py`
- **Workflow**: High-Value Claim (\$1,200) -> 2-Tier Approval (Manager + Finance) -> Budget Reservation -> Reimbursement
- **Verification details**:
  - Employee submits a \$1,200 travel claim with receipt hash via `POST /api/expenses/claims`.
  - Because amount exceeds \$1,000, approval chain creates 2 approval steps:
    1. Step 1 (Manager sign-off)
    2. Step 2 (Finance Director sign-off)
  - Manager approves Step 1: asserts `final_approval == False` (claim remains pending).
  - Finance Director approves Step 2: asserts `final_approval == True` (claim is now approved).
  - Finance Director triggers reimbursement via `POST /api/approvals/reimburse/{claim_id}`.
  - Confirms response status is `PROCESSED`, returns an internal reference like `ACH-TXN-XXXXXXXX`, and claim status flips to `REIMBURSED`.

#### 13. `test_scenario_c_split_claims_detected_and_reviewed`
- **File**: `backend/tests/test_e2e_scenarios.py`
- **Workflow**: Anomaly Detection Queue -> Finance Review -> Resolution
- **Verification details**:
  - Finance Director logs in and queries `GET /api/anomalies?anomaly_type=ROLLING_WINDOW_SPLIT_CLAIM`.
  - Verifies that pre-flagged split claim alerts exist in the queue.
  - Finance reviews an alert via `POST /api/anomalies/{alert_id}/review` with status `CONFIRMED` and review notes.
  - Confirms alert updates to `CONFIRMED` in the database.

#### 14. `test_scenario_d_missing_receipt_request_info`
- **File**: `backend/tests/test_e2e_scenarios.py`
- **Workflow**: Missing Evidence -> REVIEW Node -> Manager Requests Information -> Held in Review
- **Verification details**:
  - Employee submits a \$120 meal claim with `receipt_url = None` and `receipt_hash = None`.
  - EFCG graph flags `CNS_EXP_RECEIPT` as `REVIEW`, resulting in `NEEDS_REVIEW` overall state.
  - Manager inspects pending claim and calls `POST /api/approvals/{step_id}/request-information` with comment `"Please upload itemized receipt for catering"`.
  - Confirms request is held in review without auto-rejecting or auto-approving.

---

## 5. Frontend Build and TypeScript Verification

In addition to backend automated tests, the frontend was verified with strict TypeScript compilation and production bundling.

### Build Command
From `frontend/` directory:
```bash
npm run build
```
This runs:
```bash
tsc -b && vite build
```

### Build Output Verification
The build runs cleanly with zero TypeScript errors:
```text
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.8 building client environment for production...
transforming...
✓ 2538 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-XEySvek1.css   56.77 kB │ gzip:   9.97 kB
dist/assets/index-CobMrqbd.js   921.37 kB │ gzip: 258.87 kB
✓ built in 1.35s
```

### What This Verifies:
1. **Strict Type Safety**: All React components, API response types, and Zustand state management interfaces strictly match expected contracts.
2. **Bundle Integrity**: All Lucide icons, Tailwind CSS classes, and React Router DOM routes bundle cleanly into the `dist/` directory.
3. **No Dead or Broken Imports**: Any missing file or broken reference would cause `tsc -b` to fail immediately.

---

## 6. Manual End-to-End Verification Flow

For evaluators wanting to verify the complete user experience in a web browser, here is a 5-step manual test flow using the seeded demo personas:

| Step | Persona | Email | Purpose | What to Check |
|---|---|---|---|---|
| **1. Submit Leave** | Sarah Chen (Employee) | `sarah.chen@leaveflow.internal` | Apply for 3 days annual leave | Constraint graph visualizes all 8 nodes in green (`PASS`). Request enters `PENDING_APPROVAL`. |
| **2. Approve Leave** | Marcus Vance (Manager) | `marcus.vance@leaveflow.internal` | Review team pending queue | Marcus sees Sarah's request with live EFCG summary and clicks **Approve**. Balance commits atomically. |
| **3. Submit Expense** | Sarah Chen (Employee) | `sarah.chen@leaveflow.internal` | Submit \$1,200 conference flight | Upload receipt. SHA-256 hash displays. Graph generates 2 approval tiers. |
| **4. Multi-tier Approval & Reimbursement** | Marcus Vance + Elena Rostova (Finance) | `elena.rostova@leaveflow.internal` | Complete approvals & reimburse | Marcus approves Tier 1. Elena approves Tier 2 and clicks **Process Reimbursement**. `ACH-TXN` reference is issued. |
| **5. Audit Verification** | Dr. Patel (Auditor) | `dr.patel@leaveflow.internal` | Verify tamper-evident audit trail | Navigate to **Audit Trail** and click **Verify Chain Integrity**. System confirms 100% cryptographic validity. |

*Default password for all demo accounts: `Password123!`*

---

## 7. Test Isolation and Idempotency Notes

When writing or maintaining tests in LeaveFlow:
- **Test Database**: Tests run against the database session defined in `backend/tests/conftest.py`.
- **Dynamic Offsets**: End-to-end leave tests use dynamic future date offsets to guarantee that repeated test runs never conflict with previously committed leaves.
- **Audit Cleanup**: Any test that intentionally mutates database records (like `test_audit_chain_tamper_detection`) deletes the mutated record after the assertion, preserving audit chain integrity for subsequent tests.
- **Deterministic Seed**: The synthetic database generator uses deterministic pseudo-random seeds, ensuring reproducible test datasets across different environments.
