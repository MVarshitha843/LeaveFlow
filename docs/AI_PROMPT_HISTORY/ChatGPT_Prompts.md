# LeaveFlow — ChatGPT Prompt History

> **Note on Prompt History**: This document contains the prompts and queries used with **ChatGPT** during the planning, concept design, and architectural phases of **LeaveFlow**. Prompts where the exact conversation text was reconstructed from working notes are clearly labeled as `[Reconstructed Prompt]`. Only **ChatGPT** and **Antigravity** were used as AI tools in this project.

---

## 1. How ChatGPT Contributed to LeaveFlow

I used **ChatGPT** as my brainstorming, research, and planning partner during the initial stages of the project. Whenever I had questions about how enterprise leave and expense systems work, how to design the database models, how to structure the **Evidence-First Constraint Graph (EFCG)** algorithm, or how to avoid common pitfalls like duplicate receipt submissions and race conditions in leave balances, I consulted ChatGPT.

ChatGPT helped me:
- Understand the real-world operational problems in legacy HR and expense management software.
- Conceptualize the 6-stage EFCG decision pipeline (Intake $\rightarrow$ DAG Construction $\rightarrow$ Three-State Evaluation $\rightarrow$ Decision Synthesis $\rightarrow$ Authority Routing $\rightarrow$ Cryptographic Audit).
- Formulate the mathematical rules for business-day calculations, schedule overlap detection, rolling-window split claims, and SHA-256 hash chains.
- Design the relational database schema, ensuring clean foreign key relationships and separating balance commitments from atomic dual-ledger reservations.
- Assemble the comprehensive project requirements and specifications that were later handed over to **Antigravity** for full-stack implementation.

---

## 2. Prompt History by Development Phase

### 1. Project Idea & Problem Statement

#### [Reconstructed Prompt]
> "I want to build a combined leave and expense management platform called LeaveFlow for a hackathon. In most companies, leave and expense systems are separate and have problems like people taking more leave than they have balance for, booking overlapping leaves, submitting the same receipt twice, or splitting big expenses into smaller amounts to avoid manager approval. Can you help me define the core problem statement and suggest what features I should build so that every decision made by the system is transparent and explainable?"

---

### 2. Planning the Overall Architecture

#### [Reconstructed Prompt]
> "I want the decision engine in my project to be explainable instead of just returning a black-box 'Approved' or 'Rejected' with no reason. My idea is to use an Evidence-First Constraint Graph (EFCG) where each policy rule is evaluated as a node in a graph. Can you help me design a 6-stage architectural pipeline from when an employee submits a request to when it gets evaluated, approved by managers, and recorded in an audit trail?"

---

### 3. Choosing the Technology Stack

#### [Reconstructed Prompt]
> "Which technology stack would be best for building LeaveFlow? I want to use Python with FastAPI and SQLite (with WAL mode enabled) for the backend, and React with TypeScript and Tailwind CSS for the frontend. Is this stack good for a local hackathon project that needs to be fast and easy to run? What libraries should I use for icons, animations, and data charts?"

---

### 4. Designing the Database & Relationships

#### [Reconstructed Prompt]
> "Can you help me design the database tables for LeaveFlow? I need tables for employees, departments, cost centers, leave policies, leave balances, leave requests, corporate holidays, expense policies, expense claims, itemized expense lines, approval steps, anomaly alerts, resource reservations, and an audit trail. How should these tables be connected with foreign keys, and how can I make sure leave days and expense budgets are tracked accurately?"

---

### 5. Understanding the Evidence-First Constraint Graph (EFCG)

#### [Reconstructed Prompt]
> "Can you explain how I should implement the Evidence-First Constraint Graph in Python? How does a Directed Acyclic Graph (DAG) work in this context, and how can I use Kahn's algorithm or topological sorting to evaluate prerequisite nodes first? I want each constraint node to produce verifiable evidence (like actual numbers compared to policy thresholds) instead of just returning true or false."

---

### 6. Planning Leave Request Validation & Working Days

#### [Reconstructed Prompt]
> "When an employee applies for leave, calculating the number of days isn't just end date minus start date. How can I write a business days calculator that excludes weekends (Saturdays and Sundays) and official corporate holidays from the count? Also, how can I mathematically check if the requested date range overlaps with any other leave requests the employee has already booked?"

---

### 7. Planning Expense Claim Validation & Receipt Hashing

#### [Reconstructed Prompt]
> "For the expense management side, how can I prevent employees from uploading the exact same receipt image for multiple claims? Can I calculate a SHA-256 hash of the receipt file and check if that digest already exists in the database? Also, how should expense policies enforce category limits and require itemized line items?"

---

### 8. Understanding Three-State Decisions (PASS, FAIL, REVIEW)

#### [Reconstructed Prompt]
> "In normal systems, rules are just boolean True or False. But in LeaveFlow, I want three states: PASS, FAIL, and REVIEW. Can you explain when a rule should evaluate to PASS, when it should FAIL, and when it should flag for REVIEW? For example, if someone's claim is above a soft threshold or is missing an optional receipt, how does the engine aggregate all nodes to decide if the overall request is ELIGIBLE, NEEDS_REVIEW, or BLOCKED?"

---

### 9. Detecting Overlapping Leaves & Suspicious Split Claims

#### [Reconstructed Prompt]
> "I want to add anomaly detection algorithms. Can you help me plan two specific detectors:
> 1. Schedule Overlap Detection: How to find if an employee has conflicting leave intervals.
> 2. Rolling-Window Split-Claim Detection: If a policy requires senior manager approval for expenses over $1,000, employees might submit three $400 claims in a week from the same merchant to bypass the limit. How can I detect this clustering pattern over a 7-day rolling window without falsely labeling it as fraud?"

---

### 10. Designing Approval Workflows & Zero Self-Approval

#### [Reconstructed Prompt]
> "How should the approval hierarchy work for different roles? For example, normal employees need manager approval, but what happens if a manager submits their own leave or expense? I want to enforce strict zero self-approval so that a manager's request automatically escalates to their department head or finance. Can you help me model this approval graph traversal?"

---

### 11. Resource Reservation & Cryptographic Audit Trail

#### [Reconstructed Prompt]
> "I want to prevent race conditions where someone submits two leave requests at the same time and both get approved because the balance wasn't deducted yet. How can I implement a temporary reservation ledger that holds the days upon submission and only commits them once approved (or releases them if rejected)? Also, how can I create an append-only audit log with SHA-256 hash chaining so that anyone can verify that no historical records were tampered with?"

---

### 12. Testing Strategy, Documentation & Master Prompt Preparation

#### [Reconstructed Prompt]
> "I need to prepare a comprehensive master specification prompt that I can give to an autonomous coding assistant like Antigravity to build the entire project cleanly without cutting corners. Can you help me consolidate all our architectural decisions, database models, algorithms, UI requirements, test scenarios, and synthetic data requirements into an organized, step-by-step master prompt?"

---

## 3. Summary

ChatGPT was essential for the **conceptualization, mathematical formulation, and planning** of LeaveFlow. The discussions with ChatGPT produced the clear requirements and algorithmic foundations that were later implemented and verified by **Antigravity**.
