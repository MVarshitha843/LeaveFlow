import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

def test_scenario_a_leave_lifecycle_complete(client: TestClient, employee_token: str, manager_token: str):
    """
    Scenario A: Employee submits leave -> EFCG evaluation -> Eligible -> Manager approval -> Commitment -> Audit.
    """
    # 1. Employee submits leave
    resp = client.post(
        "/api/leave/requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "policy_id": "POL-ANNUAL",
            "start_date": "2026-12-01",
            "end_date": "2026-12-03",
            "reason": "End-of-year holiday rest"
        }
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    request_id = data["id"]
    assert data["decision_state"] in ["ELIGIBLE", "NEEDS_REVIEW"]
    assert data["status"] == "PENDING_APPROVAL"

    # 2. Verify graph endpoint reflects live node evaluations
    graph_resp = client.get(
        f"/api/decision/{request_id}/graph",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert len(graph_data["nodes"]) >= 7

    # 3. Manager approves
    # Fetch pending step
    steps_resp = client.get(
        f"/api/approvals/request/{request_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert steps_resp.status_code == 200
    steps = steps_resp.json()
    assert len(steps) >= 1
    step_id = steps[0]["id"]

    approve_resp = client.post(
        f"/api/approvals/{step_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"action": "APPROVE", "comments": "Approved. Have a great vacation!"}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["final_approval"] is True

    # 4. Check request is now APPROVED
    req_resp = client.get(
        f"/api/leave/requests/{request_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert req_resp.status_code == 200
    assert req_resp.json()["status"] == "APPROVED"

    # 5. Verify audit events recorded
    audit_resp = client.get(
        f"/api/audit/request/{request_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert audit_resp.status_code == 200
    audit_events = audit_resp.json()
    actions = [e["action"] for e in audit_events]
    assert "SUBMITTED" in actions
    assert "STEP_APPROVED" in actions

def test_scenario_b_expense_lifecycle_complete(client: TestClient, employee_token: str, manager_token: str, finance_token: str):
    """
    Scenario B: Employee submits expense -> Policy pass -> Reservation -> Manager approval -> Finance approval -> Reimbursement.
    """
    # 1. Submit $1,200 travel claim (triggers both manager + finance approval because > $1000)
    resp = client.post(
        "/api/expenses/claims",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "cost_center_id": "CC-ENG-01",
            "category": "TRAVEL",
            "merchant": "United Airlines",
            "claim_date": "2026-10-15",
            "total_amount": 1200.00,
            "description": "Flight for Q4 Tech Conference",
            "receipt_url": "/uploads/test_flight.pdf",
            "receipt_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "lines": [
                {"category": "TRAVEL", "description": "Roundtrip Airfare", "amount": 1200.00}
            ]
        }
    )
    assert resp.status_code == 200, resp.text
    claim_data = resp.json()
    claim_id = claim_data["id"]

    # 2. Fetch approval steps (should have Manager step 1, Finance step 2)
    steps_resp = client.get(
        f"/api/approvals/request/{claim_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert steps_resp.status_code == 200
    steps = steps_resp.json()
    assert len(steps) >= 2

    # Step 1: Manager approves
    mgr_step = steps[0]
    m_app = client.post(
        f"/api/approvals/{mgr_step['id']}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"action": "APPROVE", "comments": "Manager sign-off"}
    )
    assert m_app.status_code == 200
    assert m_app.json()["final_approval"] is False  # Still needs Finance!

    # Step 2: Finance approves
    fin_step = steps[1]
    f_app = client.post(
        f"/api/approvals/{fin_step['id']}/approve",
        headers={"Authorization": f"Bearer {finance_token}"},
        json={"action": "APPROVE", "comments": "Finance budget verified"}
    )
    assert f_app.status_code == 200
    assert f_app.json()["final_approval"] is True

    # 3. Finance executes reimbursement
    rmb_resp = client.post(
        f"/api/approvals/reimburse/{claim_id}",
        headers={"Authorization": f"Bearer {finance_token}"}
    )
    assert rmb_resp.status_code == 200
    rmb_data = rmb_resp.json()
    assert rmb_data["status"] == "PROCESSED"
    assert rmb_data["transaction_ref"].startswith("ACH-TXN")

    # 4. Claim status is now REIMBURSED
    c_check = client.get(
        f"/api/expenses/claims/{claim_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert c_check.status_code == 200
    assert c_check.json()["status"] == "REIMBURSED"

def test_scenario_c_split_claims_detected_and_reviewed(client: TestClient, employee_token: str, finance_token: str):
    """
    Scenario C: Potential split claims detected -> Flagged for review -> Finance review.
    """
    # Check that anomaly queue has ROLLING_WINDOW_SPLIT_CLAIM alert
    alerts_resp = client.get(
        "/api/anomalies?anomaly_type=ROLLING_WINDOW_SPLIT_CLAIM",
        headers={"Authorization": f"Bearer {finance_token}"}
    )
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # Finance reviews and confirms the alert
    rev_resp = client.post(
        f"/api/anomalies/{alert_id}/review",
        headers={"Authorization": f"Bearer {finance_token}"},
        json={"status": "CONFIRMED", "notes": "Confirmed threshold avoidance pattern."}
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["status"] == "CONFIRMED"

def test_scenario_d_missing_receipt_request_info(client: TestClient, employee_token: str, manager_token: str):
    """
    Scenario D: Missing receipt -> REVIEW status -> Manager requests info.
    """
    # Submit claim without receipt
    resp = client.post(
        "/api/expenses/claims",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "cost_center_id": "CC-ENG-01",
            "category": "MEALS",
            "merchant": "Team Catering",
            "claim_date": "2026-10-20",
            "total_amount": 120.00,
            "description": "Team lunch meeting",
            "receipt_url": None,
            "receipt_hash": None
        }
    )
    assert resp.status_code == 200
    claim_id = resp.json()["id"]

    # Manager requests information
    steps_resp = client.get(
        f"/api/approvals/request/{claim_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    step_id = steps_resp.json()[0]["id"]

    req_info = client.post(
        f"/api/approvals/{step_id}/request-information",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"action": "REQUEST_INFO", "comments": "Please upload itemized receipt for catering"}
    )
    assert req_info.status_code == 200

    # Claim is marked NEEDS_REVIEW
    c_check = client.get(
        f"/api/expenses/claims/{claim_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert c_check.json()["decision_state"] == "NEEDS_REVIEW"
