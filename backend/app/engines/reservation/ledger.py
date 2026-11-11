from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session
from backend.app.models.ledger import ResourceReservation, ResourceType, ReservationStatus
from backend.app.models.leave import LeaveBalance
from backend.app.models.employee import CostCenter, Department

class ResourceReservationLedger:
    """
    Dedicated Resource Reservation Ledger.
    Ensures safe, atomic allocation of leave days and financial expense budgets.
    Guarantees no double allocation, releases on reject/cancel, and commits on approval.
    """

    @staticmethod
    def reserve_leave(
        db: Session,
        request_id: str,
        employee_id: str,
        leave_policy_id: str,
        days: float,
        year: int = 2026
    ) -> ResourceReservation:
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_policy_id == leave_policy_id,
            LeaveBalance.year == year
        ).with_for_update().first()

        if not balance:
            raise ValueError(f"No leave balance record found for employee {employee_id} and policy {leave_policy_id}")

        available = balance.allocated_days - balance.used_days - balance.reserved_days
        if available < days:
            raise ValueError(f"Insufficient available leave balance: requested {days} days, but only {available:.1f} available")

        # Atomic reservation
        previous_available = available
        balance.reserved_days += days

        reservation = ResourceReservation(
            request_id=request_id,
            resource_type=ResourceType.LEAVE_DAYS,
            employee_id=employee_id,
            leave_policy_id=leave_policy_id,
            reserved_amount=Decimal(str(days)),
            previous_available=Decimal(str(previous_available)),
            final_committed=Decimal("0.00"),
            status=ReservationStatus.RESERVED
        )
        db.add(reservation)
        db.flush()
        return reservation

    @staticmethod
    def commit_leave(db: Session, request_id: str) -> Optional[ResourceReservation]:
        reservation = db.query(ResourceReservation).filter(
            ResourceReservation.request_id == request_id,
            ResourceReservation.resource_type == ResourceType.LEAVE_DAYS,
            ResourceReservation.status == ReservationStatus.RESERVED
        ).with_for_update().first()

        if not reservation:
            return None

        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == reservation.employee_id,
            LeaveBalance.leave_policy_id == reservation.leave_policy_id
        ).with_for_update().first()

        if balance:
            days_float = float(reservation.reserved_amount)
            balance.reserved_days = max(0.0, balance.reserved_days - days_float)
            balance.used_days += days_float

        reservation.status = ReservationStatus.COMMITTED
        reservation.final_committed = reservation.reserved_amount
        reservation.updated_at = datetime.now(timezone.utc)
        db.flush()
        return reservation

    @staticmethod
    def release_leave(db: Session, request_id: str) -> Optional[ResourceReservation]:
        reservation = db.query(ResourceReservation).filter(
            ResourceReservation.request_id == request_id,
            ResourceReservation.resource_type == ResourceType.LEAVE_DAYS,
            ResourceReservation.status == ReservationStatus.RESERVED
        ).with_for_update().first()

        if not reservation:
            return None

        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == reservation.employee_id,
            LeaveBalance.leave_policy_id == reservation.leave_policy_id
        ).with_for_update().first()

        if balance:
            days_float = float(reservation.reserved_amount)
            balance.reserved_days = max(0.0, balance.reserved_days - days_float)

        reservation.status = ReservationStatus.RELEASED
        reservation.updated_at = datetime.now(timezone.utc)
        db.flush()
        return reservation

    @staticmethod
    def reserve_expense_budget(
        db: Session,
        request_id: str,
        employee_id: str,
        cost_center_id: str,
        amount: Decimal
    ) -> ResourceReservation:
        cost_center = db.query(CostCenter).filter(
            CostCenter.id == cost_center_id
        ).with_for_update().first()

        if not cost_center:
            raise ValueError(f"Cost center {cost_center_id} not found")

        available = cost_center.budget_limit - cost_center.current_spend - cost_center.reserved_spend
        if available < amount:
            raise ValueError(
                f"Cost center budget exceeded: requested ${amount:,.2f}, "
                f"available budget is ${available:,.2f}"
            )

        previous_available = available
        cost_center.reserved_spend += amount

        # Also update parent department reserved budget if present
        dept = db.query(Department).filter(Department.id == cost_center.department_id).first()
        if dept:
            dept.reserved_budget += amount

        reservation = ResourceReservation(
            request_id=request_id,
            resource_type=ResourceType.BUDGET_AMOUNT,
            employee_id=employee_id,
            cost_center_id=cost_center_id,
            reserved_amount=amount,
            previous_available=previous_available,
            final_committed=Decimal("0.00"),
            status=ReservationStatus.RESERVED
        )
        db.add(reservation)
        db.flush()
        return reservation

    @staticmethod
    def commit_expense_budget(db: Session, request_id: str) -> Optional[ResourceReservation]:
        reservation = db.query(ResourceReservation).filter(
            ResourceReservation.request_id == request_id,
            ResourceReservation.resource_type == ResourceType.BUDGET_AMOUNT,
            ResourceReservation.status == ReservationStatus.RESERVED
        ).with_for_update().first()

        if not reservation:
            return None

        cost_center = db.query(CostCenter).filter(
            CostCenter.id == reservation.cost_center_id
        ).with_for_update().first()

        if cost_center:
            cost_center.reserved_spend = max(Decimal("0.00"), cost_center.reserved_spend - reservation.reserved_amount)
            cost_center.current_spend += reservation.reserved_amount

            dept = db.query(Department).filter(Department.id == cost_center.department_id).first()
            if dept:
                dept.reserved_budget = max(Decimal("0.00"), dept.reserved_budget - reservation.reserved_amount)
                dept.current_spend += reservation.reserved_amount

        reservation.status = ReservationStatus.COMMITTED
        reservation.final_committed = reservation.reserved_amount
        reservation.updated_at = datetime.now(timezone.utc)
        db.flush()
        return reservation

    @staticmethod
    def release_expense_budget(db: Session, request_id: str) -> Optional[ResourceReservation]:
        reservation = db.query(ResourceReservation).filter(
            ResourceReservation.request_id == request_id,
            ResourceReservation.resource_type == ResourceType.BUDGET_AMOUNT,
            ResourceReservation.status == ReservationStatus.RESERVED
        ).with_for_update().first()

        if not reservation:
            return None

        cost_center = db.query(CostCenter).filter(
            CostCenter.id == reservation.cost_center_id
        ).with_for_update().first()

        if cost_center:
            cost_center.reserved_spend = max(Decimal("0.00"), cost_center.reserved_spend - reservation.reserved_amount)
            dept = db.query(Department).filter(Department.id == cost_center.department_id).first()
            if dept:
                dept.reserved_budget = max(Decimal("0.00"), dept.reserved_budget - reservation.reserved_amount)

        reservation.status = ReservationStatus.RELEASED
        reservation.updated_at = datetime.now(timezone.utc)
        db.flush()
        return reservation
