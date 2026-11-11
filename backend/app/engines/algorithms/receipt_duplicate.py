import hashlib
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from backend.app.models.expense import ExpenseClaim, ExpenseClaimStatus

def calculate_sha256(file_bytes: bytes) -> str:
    """Computes SHA-256 hash of raw file content."""
    sha = hashlib.sha256()
    sha.update(file_bytes)
    return sha.hexdigest()

def check_duplicate_receipt(
    db: Session,
    receipt_hash: Optional[str],
    current_claim_id: Optional[str] = None
) -> Dict:
    """
    Checks if the SHA-256 receipt hash matches any existing active expense claim.
    """
    if not receipt_hash or receipt_hash.strip() == "":
        return {
            "has_duplicate": False,
            "matching_claims": [],
            "message": "No receipt hash provided."
        }

    query = db.query(ExpenseClaim).filter(
        ExpenseClaim.receipt_hash == receipt_hash,
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

    if matching_claims:
        duplicates = [
            {
                "claim_id": c.id,
                "employee_id": c.employee_id,
                "claim_date": c.claim_date.isoformat(),
                "total_amount": float(c.total_amount),
                "merchant": c.merchant,
                "status": c.status.value
            }
            for c in matching_claims
        ]
        return {
            "has_duplicate": True,
            "receipt_hash": receipt_hash,
            "matching_claims": duplicates,
            "message": f"Duplicate receipt detected! Identical SHA-256 hash matched claim(s): " +
                       ", ".join(d["claim_id"] for d in duplicates)
        }

    return {
        "has_duplicate": False,
        "receipt_hash": receipt_hash,
        "matching_claims": [],
        "message": "Receipt hash is unique."
    }
