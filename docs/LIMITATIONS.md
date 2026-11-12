# System Limitations and Boundaries

This document provides a transparent and realistic overview of the current boundaries, limitations, and future improvements for LeaveFlow.

As a student-built project for the YottaFlex AI submission, we believe it is essential to be completely honest about what is implemented, what is simulated, and what was intentionally left out of scope for a hackathon prototype.

---

## 1. Summary of System Boundaries

LeaveFlow was built to demonstrate an **Evidence-First Constraint Graph (EFCG)** architecture—replacing black-box AI approvals with deterministic, explainable, and tamper-evident constraint verification.

While the core constraint engine, dual-ledger reservation system, cryptographic audit logging, and modern web application are fully implemented and verified with automated tests, several real-world enterprise integrations (such as actual bank transfers, live email delivery, and OCR document scanning) are intentionally simulated or out of scope.

---

## 2. Implemented vs. Incomplete / Out-of-Scope Feature Matrix

The following table distinguishes what is fully functional in the codebase versus what is simulated or planned for future development:

| Feature Domain | Implemented in LeaveFlow | Boundary / Not Implemented | Reason / Production Need |
|---|---|---|---|
| **EFCG Decision Engine** | 8-node Leave DAG, 9-node Expense DAG, 3-state output (`PASS`, `FAIL`, `REVIEW`), and decision explanations. | No dynamic visual rule builder in the UI for HR admins to add arbitrary new DAG nodes without code. | DAG topologies are defined in Python code (`builder.py`) for type safety and deterministic execution. |
| **Dual-Ledger Reservation** | Two-phase commit (`RESERVED` -> `COMMITTED` / `RELEASED`) preventing balance overdraws and budget races. | Local database transactions only; no distributed multi-datacenter consensus (e.g., Raft or 2PC across microservices). | The project runs as a modular monolith on a single database. |
| **Leave Management** | Business day calculation, public holiday exclusions, overlapping leave detection, and manager approval routing. | Hourly leave tracking (half-day or partial hours) and complex statutory leave workflows (e.g., US FMLA, parental leave documentation). | Designed around full business-day requests for clean algorithmic verification. |
| **Expense Management** | Multi-tier approval hierarchy (\$1,000 threshold), receipt upload, SHA-256 duplicate detection, and rolling split-claim detection. | No Optical Character Recognition (OCR) to parse printed receipt text, line items, or tax amounts from photos/PDFs. | Receipt check uses byte-level cryptographic hashing rather than machine vision parsing. |
| **Reimbursements** | Finance disbursement flow, state transition to `REIMBURSED`, and synthetic transaction reference generation. | No live banking rails, Stripe Treasury, Plaid, or automated ACH clearing house connections. | Academic prototype; executing real financial transactions is out of scope and requires corporate banking credentials. |
| **Notifications** | In-app notification queue stored in SQLite `notifications` table, visible via the notification bell. | No live SMTP email dispatch (SendGrid/SES) and no corporate messaging webhooks (Slack/Teams). | Avoids dependencies on external paid third-party communication services. |
| **Cryptographic Audit** | Tamper-evident SHA-256 hash chaining, sequential verification endpoint, and tamper detection test. | No Hardware Security Module (HSM) signing or public blockchain notarization. | Cryptographic hashing is implemented in application software. |
| **Authentication & RBAC** | JWT authentication (HS256), password hashing via bcrypt, 5 distinct role personas, and role-guarded endpoints. | No Multi-Factor Authentication (MFA / TOTP), no SAML 2.0 / OAuth2 enterprise SSO, and no self-service password reset. | Demo convenience and hackathon evaluation focus. |

---

## 3. Synthetic Dataset and Demo Data

### Nature of the Data
All data currently stored in `data/leaveflow.db` is **synthetic**, generated deterministically using the Python `Faker` library and custom seeding logic in `scripts/generate_data.py`.

### Volume and Characteristics:
- **400 Employees**: Distributed across 5 departments (Engineering, Product, Marketing, Sales, Human Resources) and 8 cost centers.
- **Reporting Hierarchy**: Structured tree where every employee reports to a designated manager up to department heads and executive directors.
- **802 Historical Leaves**: Covering approved, rejected, and pending leave requests across calendar years 2025 and 2026.
- **1,005 Historical Expenses**: Spanning categories like Travel, Meals, Equipment, Software, and Training.
- **7 Ground-Truth Anomaly Scenarios**: Injected patterns specifically designed to test edge cases (duplicate receipt collision, rolling 7-day split claims, overlapping leaves, and high-value approvals).

*Note: No real corporate or employee personally identifiable information (PII) is contained in the repository.*

---

## 4. Authentication and Security Limitations

While authentication follows standard token-based practices, several production hardening measures are omitted:

1. **Token Storage**:
   - Access tokens (JWT) are stored in the browser's `localStorage` via Zustand (`useAuthStore`).
   - In high-security production environments, storing sensitive tokens in `localStorage` makes them susceptible to cross-site scripting (XSS) attacks. A production deployment would use `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
2. **Shared Demo Password**:
   - All 400 pre-seeded employees share the same default demo password (`Password123!`). This was chosen so evaluators can easily log into any role persona without needing separate credential lookup tables.
3. **No Multi-Factor Authentication (MFA / 2FA)**:
   - There is no support for SMS codes, authenticator apps (TOTP), or hardware security keys (WebAuthn / FIDO2).
4. **No Password Reset Flow**:
   - There are no endpoints for "Forgot Password" or email confirmation links because external email delivery is not configured.
5. **No Single Sign-On (SSO)**:
   - The application does not connect to corporate identity providers such as Google Workspace, Microsoft Entra ID (Azure AD), or Okta via SAML or OIDC.

---

## 5. Receipt Verification and Anomaly Detection Limitations

### Receipt Verification (SHA-256 Hashing)
- **What it does**: When an employee uploads a receipt file, the backend reads the raw bytes, computes a SHA-256 hexadecimal hash, and checks whether that exact byte sequence has been attached to any previous claim in the database.
- **Limitation**:
  - SHA-256 is an **exact binary match**. If an employee takes a photo of a paper receipt and uploads it twice, it will be caught.
  - However, if the employee slightly edits the file (e.g., cropping by 1 pixel, taking a second photo from a different angle, or saving a PNG as a JPG), the byte hash completely changes.
  - LeaveFlow does **not** currently use Optical Character Recognition (OCR) or computer vision to extract vendor names, transaction dates, or itemized totals from images.

### Split-Claim Detection (Rolling-Window Heuristic)
- **What it does**: The algorithm searches for expense claims by the same employee in the same category or merchant within a 7-day sliding window. If the cumulative sum exceeds the single-transaction approval threshold (\$1,000), it flags the claim as a suspicious split.
- **Limitation**:
  - This is a **rule-based mathematical heuristic**, not an AI or machine learning model.
  - Legitimate business expenses (for example, an employee paying for four nights of hotel accommodation as four separate daily checkout invoices) will trigger the heuristic even though they are not fraudulent.
  - For this reason, LeaveFlow intentionally routes these claims to the `NEEDS_REVIEW` anomaly queue for human compliance verification rather than auto-rejecting them.

---

## 6. Decision Engine and Rule Configuration Boundaries

1. **Code-Defined DAG Topologies**:
   - The structure of the Leave DAG (8 nodes) and Expense DAG (9 nodes) is defined in Python code (`backend/app/engines/constraint_graph/builder.py`).
   - While policy thresholds (maximum days per leave type, single-claim approval limits, required notice days) can be adjusted via database records or API endpoints, adding an entirely new type of constraint (e.g., "Check whether employee has completed mandatory safety training") requires writing a new Python node class and registering it in the builder.
2. **Absence of a Visual Drag-and-Drop Editor**:
   - There is currently no web-based visual editor allowing non-technical HR administrators to create custom workflow graphs dynamically in the browser.

---

## 7. External Integrations (Not Implemented)

To maintain a self-contained, reproducible project that runs locally without paid API keys, the following external services are simulated:

1. **Banking and ACH Payment Rails**:
   - When a Finance Director approves and processes a reimbursement, LeaveFlow changes the claim status to `REIMBURSED`, records an audit event, and generates an internal transaction identifier (e.g., `ACH-TXN-C7B9E21A4F0D`).
   - No money is moved. There is no connection to real-world payment APIs like Stripe Treasury, Modern Treasury, or Plaid.
2. **Email and SMS Delivery (SMTP)**:
   - When an approval request is created or when a manager clicks "Request Information", the system writes a notification row into the database `notifications` table.
   - Notifications appear in the frontend navigation bar, but no real emails or SMS messages are dispatched to external inboxes.
3. **Calendar Synchronization**:
   - Approved leaves do not automatically sync with external Google Calendar or Microsoft Outlook Exchange calendars via iCal feeds.

---

## 8. Database and Scalability Boundaries

1. **SQLite Database**:
   - LeaveFlow uses SQLite configured in Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and foreign key enforcement (`PRAGMA foreign_keys = ON`).
   - SQLite is excellent for local development, testing, and single-instance demonstrations because it requires zero server setup.
   - However, SQLite serializes write transactions with a database-level lock. While WAL mode allows many concurrent readers, a high-volume production deployment with thousands of concurrent writers would need to be migrated to **PostgreSQL**.
2. **Single-Node In-Memory Operations**:
   - The backend runs as a single Uvicorn instance without Redis for distributed session caching or distributed task queues (e.g., Celery).

---

## 9. Future Roadmap

If LeaveFlow were developed into a commercial enterprise product, the following enhancements would be prioritized:

### 1. Multimodal AI Receipt Parsing (OCR)
- Integrate a vision model (such as Gemini 2.5 Flash or Google Cloud Document AI) to automatically extract merchant name, transaction date, line items, and tax amounts directly from receipt PDFs or smartphone photos, comparing the extracted data against the claim form.

### 2. Visual Policy Graph Studio
- Build a React-based visual drag-and-drop canvas (using React Flow) allowing HR and Finance administrators to create custom constraint graphs, connect nodes, and adjust approval thresholds without writing Python code.

### 3. Production Security Hardening
- Migrate JWT storage to secure `HttpOnly` cookies.
- Add enterprise Single Sign-On (SAML 2.0 / OIDC) for Okta and Google Workspace.
- Implement Time-based One-Time Password (TOTP) two-factor authentication.

### 4. Enterprise Integrations
- Connect to corporate email servers via SMTP or SendGrid for real-time manager alerts.
- Connect to Slack and Microsoft Teams webhooks so managers can approve leaves with a single click in chat.
- Add Google Calendar / Microsoft Outlook calendar integration for approved leaves.

### 5. Distributed Infrastructure
- Migrate from SQLite to **PostgreSQL** with connection pooling (e.g., asyncpg or pgBouncer).
- Add **Redis** for distributed session management and rate limiting.
