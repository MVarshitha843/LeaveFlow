import pytest
from decimal import Decimal
from backend.app.engines.reservation.ledger import ResourceReservationLedger
from backend.app.engines.audit.service import AuditService
from backend.app.models.ledger import ReservationStatus
from backend.app.models.leave import LeaveBalance
from backend.app.models.employee import CostCenter
from backend.app.models.audit import AuditEvent

def test_leave_reservation_commit_and_release(db_session):
    emp_id = "EMP-000005"
    policy_id = "POL-ANNUAL"
    test_req_id = "TEST-RES-LVE-01"

    # Get balance
    bal = db_session.query(LeaveBalance).filter(
        LeaveBalance.employee_id == emp_id,
        LeaveBalance.leave_policy_id == policy_id
    ).first()
    init_reserved = bal.reserved_days
    init_used = bal.used_days

    # 1. Reserve 3 days
    res = ResourceReservationLedger.reserve_leave(
        db=db_session,
        request_id=test_req_id,
        employee_id=emp_id,
        leave_policy_id=policy_id,
        days=3.0
    )
    assert res.status == ReservationStatus.RESERVED
    db_session.refresh(bal)
    assert bal.reserved_days == init_reserved + 3.0

    # 2. Commit
    committed_res = ResourceReservationLedger.commit_leave(db_session, test_req_id)
    assert committed_res.status == ReservationStatus.COMMITTED
    db_session.refresh(bal)
    assert bal.reserved_days == init_reserved
    assert bal.used_days == init_used + 3.0

    # 3. Test release on rejection/cancel
    test_req_cancel = "TEST-RES-LVE-02"
    res2 = ResourceReservationLedger.reserve_leave(
        db=db_session,
        request_id=test_req_cancel,
        employee_id=emp_id,
        leave_policy_id=policy_id,
        days=2.0
    )
    db_session.refresh(bal)
    assert bal.reserved_days == init_reserved + 2.0

    released_res = ResourceReservationLedger.release_leave(db_session, test_req_cancel)
    assert released_res.status == ReservationStatus.RELEASED
    db_session.refresh(bal)
    assert bal.reserved_days == init_reserved

def test_prevent_double_allocation_or_overdraw(db_session):
    emp_id = "EMP-000005"
    policy_id = "POL-ANNUAL"

    # Try to reserve 9999 days (exceeds balance)
    with pytest.raises(ValueError) as excinfo:
        ResourceReservationLedger.reserve_leave(
            db=db_session,
            request_id="OVERDRAW-TEST",
            employee_id=emp_id,
            leave_policy_id=policy_id,
            days=9999.0
        )
    assert "Insufficient available leave balance" in str(excinfo.value)

def test_tamper_evident_audit_chain_verification(db_session):
    # Record test event
    ev1 = AuditService.record_event(
        db=db_session,
        entity_type="TEST",
        entity_id="TEST-001",
        action="VERIFY_CHECK",
        payload={"data": "sample_1"},
        actor_id="TEST_ACTOR"
    )
    db_session.commit()

    # Verify chain integrity
    integrity = AuditService.verify_integrity(db_session)
    assert integrity["is_valid"] is True
    assert integrity["total_events"] > 0

def test_audit_chain_tamper_detection(db_session):
    # Record event
    ev = AuditService.record_event(
        db=db_session,
        entity_type="TEST",
        entity_id="TEST-TAMPER-01",
        action="GENUINE_ACTION",
        payload={"sensitive_budget": 500},
        actor_id="TEST_ACTOR"
    )
    db_session.commit()

    # Intentionally tamper with payload in the database directly
    ev_record = db_session.query(AuditEvent).filter(AuditEvent.id == ev.id).first()
    ev_record.payload_json = '{"sensitive_budget": 999999}'
    db_session.commit()

    # Audit verification must detect tampering!
    tamper_check = AuditService.verify_integrity(db_session)
    assert tamper_check["is_valid"] is False
    assert tamper_check["error_type"] == "PAYLOAD_TAMPERED"
    assert tamper_check["corrupted_event_id"] == ev.id
