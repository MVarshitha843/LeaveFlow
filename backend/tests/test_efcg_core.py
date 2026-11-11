import pytest
from datetime import date
from decimal import Decimal
from backend.app.engines.algorithms.business_days import calculate_business_days
from backend.app.engines.algorithms.interval_overlap import check_interval_overlap
from backend.app.engines.algorithms.split_claim import detect_split_claims
from backend.app.engines.algorithms.receipt_duplicate import check_duplicate_receipt, calculate_sha256
from backend.app.engines.algorithms.authority_traversal import resolve_approval_chain
from backend.app.engines.constraint_graph.builder import build_leave_constraint_graph, build_expense_constraint_graph
from backend.app.engines.decision.synthesizer import DecisionSynthesizer
from backend.app.models.decision import ConstraintResult

def test_business_days_with_holidays():
    # Jan 15 (Thu) to Jan 21 (Wed) 2026: 7 calendar days
    # Weekend: Jan 17 (Sat), Jan 18 (Sun) = 2 days
    # Holiday: Jan 19 (Mon, MLK Day) = 1 day
    # Net business days: 4 days (Thu, Fri, Tue, Wed)
    holiday_set = {date(2026, 1, 19)}
    result = calculate_business_days(date(2026, 1, 15), date(2026, 1, 21), holiday_set)
    
    assert result["valid_range"] is True
    assert result["calendar_days"] == 7
    assert result["weekend_days"] == 2
    assert result["holiday_days"] == 1
    assert result["business_days"] == 4.0
    assert len(result["excluded_dates"]) == 3

def test_interval_overlap_detection(db_session):
    # Employee EMP-000004 has overlapping leaves injected July 6 - July 10
    overlap_res = check_interval_overlap(
        db=db_session,
        employee_id="EMP-000004",
        start_date=date(2026, 7, 7),
        end_date=date(2026, 7, 9)
    )
    assert overlap_res["has_overlap"] is True
    assert len(overlap_res["conflicts"]) > 0

    # Non-overlapping range
    clean_res = check_interval_overlap(
        db=db_session,
        employee_id="EMP-000004",
        start_date=date(2027, 2, 1),
        end_date=date(2027, 2, 5)
    )
    assert clean_res["has_overlap"] is False

def test_split_claim_suspicious_detector(db_session):
    # EMP-000005 has claims at BestBuy Corporate Tech around May 14-16
    split_res = detect_split_claims(
        db=db_session,
        employee_id="EMP-000005",
        claim_date=date(2026, 5, 17),
        current_amount=Decimal("910.00"),
        category="EQUIPMENT",
        merchant="BestBuy Corporate Tech",
        cost_center_id="CC-ENG-01",
        window_days=7,
        threshold=1000.0
    )
    assert split_res["is_suspicious_split"] is True
    assert split_res["pattern_type"] == "ROLLING_WINDOW_SPLIT_CLAIM"
    assert split_res["cumulative_amount"] > 1000.0

def test_receipt_duplicate_detection(db_session):
    test_bytes = b"SAMPLE_RECEIPT_CONTENT"
    h = calculate_sha256(test_bytes)
    assert len(h) == 64

    # Using duplicate hash from seeded generator
    dup_hash = calculate_sha256(b"DUPLICATE_RECEIPT_FINGERPRINT_FOR_TESTING")
    dup_check = check_duplicate_receipt(db_session, dup_hash)
    assert dup_check["has_duplicate"] is True
    assert len(dup_check["matching_claims"]) >= 1

def test_authority_graph_zero_self_approval(db_session):
    # Employee EMP-000005 should route to manager EMP-000004
    chain = resolve_approval_chain(db_session, "EMP-000005", "LEAVE", 3.0)
    assert len(chain) >= 1
    for step in chain:
        assert step["approver_id"] != "EMP-000005", "Self-approval invariant violated!"

    # Admin EMP-000001 (who has no manager) should route to another officer, never self
    admin_chain = resolve_approval_chain(db_session, "EMP-000001", "EXPENSE", 250.0)
    for step in admin_chain:
        assert step["approver_id"] != "EMP-000001", "Self-approval invariant violated for admin!"

def test_efcg_leave_graph_evaluation(db_session):
    nodes = build_leave_constraint_graph(
        db=db_session,
        employee_id="EMP-000005",
        policy_id="POL-ANNUAL",
        start_date=date(2026, 11, 16),
        end_date=date(2026, 11, 20),
        reason="Family vacation"
    )
    result = DecisionSynthesizer.execute_graph(
        nodes=nodes,
        db=db_session,
        request_id="TEST-EVAL-01",
        request_type="LEAVE",
        persist_evaluations=False
    )
    assert result["decision_state"] in ["ELIGIBLE", "NEEDS_REVIEW"]
    assert result["summary"]["total_constraints"] == len(nodes)
    assert "explanation" in result
    assert len(result["execution_order"]) == len(nodes)
