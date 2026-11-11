from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from backend.app.models.expense import ExpenseClaim, ExpenseClaimStatus
from backend.app.core.config import settings

def detect_split_claims(
    db: Session,
    employee_id: str,
    claim_date: date,
    current_amount: Decimal,
    category: str,
    merchant: str,
    cost_center_id: str,
    current_claim_id: Optional[str] = None,
    window_days: Optional[int] = None,
    threshold: Optional[float] = None
) -> Dict:
    """
    Suspicious-Pattern Detector for Split Claims.
    Identifies if an employee has submitted multiple claims with similar attributes
    (same merchant or same category/cost-center) within a rolling date window,
    where individual claims fall below approval limits, but their cumulative amount
    exceeds the threshold.

    IMPORTANT: Flags as 'REVIEW' (suspicious pattern requiring human review),
    never automatically labeled as fraud.
    """
    if window_days is None:
        window_days = settings.SPLIT_CLAIM_WINDOW_DAYS
    if threshold is None:
        threshold = settings.EXPENSE_MANAGER_THRESHOLD

    threshold_dec = Decimal(str(threshold))
    start_window = claim_date - timedelta(days=window_days)
    end_window = claim_date + timedelta(days=window_days)

    normalized_merchant = merchant.strip().lower()

    # Query existing claims in the window
    query = db.query(ExpenseClaim).filter(
        ExpenseClaim.employee_id == employee_id,
        ExpenseClaim.claim_date >= start_window,
        ExpenseClaim.claim_date <= end_window,
        ExpenseClaim.status.in_([
            ExpenseClaimStatus.SUBMITTED,
            ExpenseClaimStatus.PENDING_APPROVAL,
            ExpenseClaimStatus.APPROVED,
            ExpenseClaimStatus.REIMBURSED
        ])
    )

    if current_claim_id:
        query = query.filter(ExpenseClaim.id != current_claim_id)

    matching_claims = query.all()

    # Filter by merchant or category+cost center
    correlated_claims: List[Dict] = []
    cumulative_amount = current_amount

    for claim in matching_claims:
        is_same_merchant = claim.merchant.strip().lower() == normalized_merchant
        is_same_category_cc = (claim.category.value == category and claim.cost_center_id == cost_center_id)

        if is_same_merchant or is_same_category_cc:
            correlated_claims.append({
                "claim_id": claim.id,
                "claim_date": claim.claim_date.isoformat(),
                "merchant": claim.merchant,
                "category": claim.category.value,
                "cost_center_id": claim.cost_center_id,
                "amount": float(claim.total_amount),
                "match_reason": "Identical Merchant" if is_same_merchant else "Same Category & Cost Center"
            })
            cumulative_amount += Decimal(str(claim.total_amount))

    # Evaluate pattern:
    # Pattern triggers if there are other correlated claims AND cumulative exceeds threshold AND current is below threshold
    is_pattern_detected = (
        len(correlated_claims) > 0 and
        cumulative_amount > threshold_dec and
        current_amount < threshold_dec
    )

    if is_pattern_detected:
        return {
            "is_suspicious_split": True,
            "pattern_type": "ROLLING_WINDOW_SPLIT_CLAIM",
            "window_days": window_days,
            "threshold": float(threshold_dec),
            "current_amount": float(current_amount),
            "cumulative_amount": float(cumulative_amount),
            "correlated_claim_count": len(correlated_claims),
            "correlated_claims": correlated_claims,
            "explanation": (
                f"Suspicious split claim pattern detected: {len(correlated_claims) + 1} claims "
                f"within {window_days} days total ${cumulative_amount:,.2f}, exceeding the "
                f"${threshold_dec:,.2f} approval threshold. Marked for human review."
            )
        }

    return {
        "is_suspicious_split": False,
        "pattern_type": None,
        "window_days": window_days,
        "threshold": float(threshold_dec),
        "current_amount": float(current_amount),
        "cumulative_amount": float(cumulative_amount),
        "correlated_claim_count": len(correlated_claims),
        "correlated_claims": [],
        "explanation": "No suspicious split claim patterns detected in rolling window."
    }
