# LeaveFlow â€” Design Decisions & Trade-Offs

> **Document Scope**: Key architectural and technical design decisions made while building LeaveFlow.
> **Audience**: Hackathon judges, technical evaluators, and reviewers.
> **Perspective**: A student developer explaining why specific technologies, patterns, and trade-offs were chosen.

---

## 1. Why This Technology Stack Was Selected

When choosing the stack for LeaveFlow, the goal was to pick technologies that are fast to run locally, reliable, and type-safe across both the frontend and backend.

### Backend: Python with FastAPI, Pydantic, and SQLAlchemy
- **Why FastAPI?** I wanted a backend that is both fast and strictly typed. FastAPI automatically checks incoming request data against Pydantic schemas, handles asynchronous endpoints cleanly, and automatically generates interactive Swagger documentation at `/docs`. This made testing endpoints during development very straightforward.
- **Why SQLAlchemy 2.0?** SQLAlchemy gave me a clean way to define database relationships with foreign keys while letting me write type-safe queries. It also made it easy to write database transactions for atomic balance reservations.
- **Why SQLite with Write-Ahead Logging (WAL)?** For a hackathon evaluation, requiring the judge to install and configure a PostgreSQL or MySQL server adds unnecessary setup hurdles. SQLite requires zero configuration because it runs as a local file (`data/leaveflow.db`). By enabling **Write-Ahead Logging (WAL)** via `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;`, SQLite allows multiple readers to read the database at the same time while a write is occurring, completely eliminating typical SQLite lock errors.

### Frontend: React 19, TypeScript, Vite, and Tailwind CSS v4
- **Why React with Vite?** Vite starts up in milliseconds and provides instant Hot Module Replacement (HMR). React 19 with functional components and TypeScript ensures that every data model coming from the backend matches the frontend state without runtime type errors.
- **Why Tailwind CSS v4?** Tailwind allowed me to build a custom, cohesive **White and Blue Enterprise SaaS design system** without writing thousands of lines of custom CSS files. It kept padding, colors, rounded cards, and typography completely consistent across all 14 pages.
- **Why Framer Motion & Lucide Icons?** Framer Motion provides smooth micro-interactions (modal popups, card transitions) without causing layout jank, and Lucide React provides modern, clean iconography for enterprise dashboards.

---

## 2. Why a Rule-Based Explainable Engine (Instead of LLMs or Simple If/Else)

Many modern applications attempt to throw a Large Language Model (LLM) at approval workflows. In LeaveFlow, I deliberately avoided using an LLM for core decision logic for three practical reasons:

1. **Determinism**: In HR and financial compliance, a policy decision must be 100% deterministic. If an employee applies for 3 days of leave with a 10-day balance, the outcome should always be the exact same every single time. LLMs can hallucinate or produce slightly different outputs across runs.
2. **Execution Latency**: The EFCG engine in LeaveFlow evaluates all 8 leave constraint nodes in under **2 milliseconds**. Calling a remote LLM API would introduce a 1 to 2-second delay for every check, which is too slow for real-time pre-validation while typing.
3. **Auditable Proof**: A manager or auditor cannot verify a vague natural-language guess from an AI model. They need mathematical, verifiable proof (e.g. *"Actual available balance: 16.0 days $\ge$ Requested: 4.0 days"*).

At the same time, simple hardcoded `if/else` checks were not enough because they break when rules depend on each other and they stop evaluating at the first error without giving full context. Modeling rules as a **Directed Acyclic Graph (DAG)** gives the best of both worlds: complete determinism with deep, multi-node explainability.

---

## 3. Why EFCG Uses Three States: PASS, FAIL, and REVIEW

In traditional boolean rule engines, an evaluation can only result in `True` or `False`. I found that this binary model is too rigid for real enterprise operations:

- **Why `PASS`?** All empirical conditions are satisfied with zero ambiguity (e.g., requested days are within balance, employee status is active).
- **Why `FAIL`?** A hard policy boundary was violated that cannot be bypassed (e.g., balance is negative, receipt hash is an exact duplicate of an existing claim, or leave start date is after end date). The request is blocked.
- **Why `REVIEW`?** In real companies, many situations require human managerial discretion rather than an outright rejection. For example:
  - An expense claim of $1,200 is completely legitimate, but because it exceeds $1,000, policy requires a second approval from Finance.
  - An employee forgot to attach an optional receipt for a small $20 meal.
  - An employee submitted two $400 claims in the same week from the same vendor, triggering a suspicious split-claim heuristic.

If the engine only had PASS and FAIL, these cases would either have to be automatically rejected (frustrating employees) or automatically passed (causing financial compliance risk). The `REVIEW` state allows the engine to flag soft constraints and package them into an **evidence dossier** for human review.

---

## 4. Why ELIGIBLE and APPROVED are Separate States

A core architectural principle in LeaveFlow is that **a request being `ELIGIBLE` does NOT mean it is `APPROVED`**:

$$\text{ELIGIBLE} \ne \text{APPROVED}$$

- **`ELIGIBLE`** is an **algorithmic finding**. It means the EFCG engine checked all policy constraints, confirmed balance headroom, verified zero schedule overlaps, and found zero duplicate receipts. The system has verified that the request satisfies company policies.
- **`APPROVED`** is an **organizational human decision**. A manager might need to reject a request even if the employee has 20 days of available balance because two other team members are already on leave that week, or because a critical project deadline falls on those dates.

By clearly separating automated eligibility from human approval authority:
1. The engine acts as an assistant to the manager, pre-validating facts so the manager doesn't have to manually count days or check balances.
2. Human managers retain full authority and accountability over team scheduling and department budget sign-offs.

---

## 5. How Missing Evidence is Handled

When evaluating constraint nodes, the engine checks whether required evidence is present:
- **Mandatory Evidence**: If a policy requires a receipt (e.g. any claim over $50) and no receipt file or hash is attached, the node evaluates to `FAIL` (or flags as a blocking policy non-conformance), moving the request to `BLOCKED`.
- **Discretionary / Soft Evidence**: If a claim is under the receipt threshold or an optional field is missing, the node evaluates to `REVIEW`. The request moves to `NEEDS_REVIEW`, and the manager has the option to click **"Request Info"** in the approval queue, allowing the employee to upload documentation without restarting the application.

---

## 6. Why Suspicious Split Claims are Flagged for REVIEW (Not Automatic Fraud)

One of the anomaly detectors in LeaveFlow detects **rolling-window split claims**:
If a policy requires higher-level finance approval for expenses over $1,000, someone might submit two claims of $600 from the same airline within 4 days to stay under the $1,000 threshold.

I deliberately designed this detector to flag the claim as **`REVIEW`**, rather than automatically classifying the employee as fraudulent:
- Multiple transactions from the same merchant within a 7-day window could be completely genuine (for example, booking a flight out on Monday and a return flight on Thursday, or taking multiple Uber rides during a multi-day conference).
- Automated software should never accuse an employee of fraud without human verification.
- By flagging it as `REVIEW`, the engine brings the 7-day cumulative total ($1,200) to the manager and finance controller's attention so they can review the receipts together and make an informed decision.

---

## 7. Why Dual-Ledger Resource Reservations Are Used

In early testing, I realized that directly deducting balances upon final approval creates a major concurrency vulnerability: an employee with 3 days of leave could submit two separate 3-day requests within minutes. Because both requests see 3 days available, both get validated as eligible.

I introduced the **Dual-Ledger Reservation System** in `backend/app/engines/reservation/ledger.py`:
- We do not deduct from `used_days` until final sign-off.
- Instead, upon submission, the requested amount is held in `resource_reservations` with status `RESERVED`, and `leave_balances.reserved_days` is incremented.
- The available headroom formula is:
  $$\text{Available Headroom} = \text{Allocated} - (\text{Used} + \text{Reserved})$$
- Because the reservation happens inside an immediate database transaction, any second request submitted a second later sees that available headroom is zero and is immediately blocked.
- If the manager rejects the request, the reservation status changes to `RELEASED` and the headroom is immediately restored.

---

## 8. Why a Hash-Linked Cryptographic Audit Trail is Important

In many enterprise tools, audit logs are simple rows in a database table: `INSERT INTO logs VALUES (...)`. The problem with this approach is that anyone with direct database access (or an attacker with SQL injection) can update rows, change approval amounts, delete records, or insert fake approvals without anyone knowing.

LeaveFlow solves this with a **cryptographic SHA-256 hash chain**:
- Every audit event references the `current_hash` of the previous block as its `previous_hash`.
- The event's hash is computed over the previous hash, timestamp, actor ID, action, and the exact JSON payload.
- If anyone changes a single character in a past event's payload, the hash chain breaks at that point.
- The `/api/audit/verify` endpoint recalculates the expected hashes across the entire history in sequence. If any payload was altered, it flags `PAYLOAD_TAMPERED` and points to the exact corrupted record.

---

## 9. Design Trade-Offs & Alternatives Considered

| Decision | What I Chose | Alternative Considered | Why I Chose This Approach |
| :--- | :--- | :--- | :--- |
| **Database** | SQLite with WAL mode | PostgreSQL / MySQL | SQLite runs zero-setup locally without requiring judges to install database servers. WAL mode provides concurrent read-write support. |
| **Receipt Verification** | SHA-256 Binary Hash | OCR / AI Vision Model | SHA-256 is instant, 100% deterministic, and requires zero paid third-party API keys or heavy GPU libraries. |
| **Reimbursement** | Internal ACH reference generation | Real Stripe / Plaid API | Hackathon projects should not execute real money transfers. Generating structured reference codes (`ACH-TXN-...`) accurately simulates banking without financial risk. |
| **Pre-Validation** | Client-side dry-run API | Pure frontend calculation | Calculating working days and overlaps on the client leads to duplicated business logic. Calling `/api/leave/dry-run` ensures the backend engine remains the single source of truth. |
| **Audit Verification** | Application SHA-256 Chain | Public Blockchain (Ethereum/Solana) | Public blockchains introduce transaction gas fees, public privacy leaks of employee data, and network latency. An application-level hash chain provides identical tamper detection with zero cost. |
