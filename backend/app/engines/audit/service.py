import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditEvent

GENESIS_HASH = "0" * 64
_audit_lock = threading.Lock()

class AuditService:
    """
    Application-Level Tamper-Evident Hash Audit Ledger.
    Maintains an append-only cryptographic chain of operational events.
    Every event references the SHA-256 hash of its predecessor.
    Any retroactive payload modification, event deletion, or insertion breaks the chain.
    """

    @staticmethod
    def _compute_hash(
        previous_hash: str,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_id: Optional[str],
        timestamp_str: str,
        payload_str: str
    ) -> str:
        raw = f"{previous_hash}|{entity_type}|{entity_id}|{action}|{actor_id or 'SYSTEM'}|{timestamp_str}|{payload_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: Dict[str, Any],
        actor_id: Optional[str] = "SYSTEM"
    ) -> AuditEvent:
        with _audit_lock:
            # Fetch latest event to get predecessor hash
            latest_event = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
            previous_hash = latest_event.current_hash if latest_event else GENESIS_HASH

            now_utc = datetime.now(timezone.utc)
            timestamp_str = now_utc.isoformat()
            canonical_payload = json.dumps(payload, sort_keys=True)

            current_hash = cls._compute_hash(
                previous_hash=previous_hash,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_id=actor_id,
                timestamp_str=timestamp_str,
                payload_str=canonical_payload
            )

            event = AuditEvent(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_id=actor_id or "SYSTEM",
                previous_hash=previous_hash,
                current_hash=current_hash,
                payload_json=canonical_payload,
                timestamp=now_utc
            )
            db.add(event)
            db.flush()
            return event

    @classmethod
    def verify_integrity(cls, db: Session) -> Dict[str, Any]:
        """
        Validates the entire audit chain from genesis to head.
        Detects payload tampering, deleted events, and broken pointer chains.
        """
        events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()

        if not events:
            return {
                "is_valid": True,
                "total_events": 0,
                "head_hash": GENESIS_HASH,
                "message": "Audit chain is empty and valid (Genesis state)."
            }

        expected_prev_hash = GENESIS_HASH

        for idx, event in enumerate(events):
            # Check 1: Predecessor link integrity
            if event.previous_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "error_type": "BROKEN_LINK_OR_MISSING_EVENT",
                    "corrupted_event_id": event.id,
                    "event_index": idx,
                    "expected_previous_hash": expected_prev_hash,
                    "recorded_previous_hash": event.previous_hash,
                    "message": f"Integrity failure at event #{event.id}: Previous hash does not match predecessor hash."
                }

            # Check 2: Re-compute hash from payload to detect tampering
            timestamp_str = event.timestamp.replace(tzinfo=timezone.utc).isoformat() if event.timestamp.tzinfo is None else event.timestamp.isoformat()
            recomputed = cls._compute_hash(
                previous_hash=event.previous_hash,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                actor_id=event.actor_id,
                timestamp_str=timestamp_str,
                payload_str=event.payload_json
            )

            if recomputed != event.current_hash:
                return {
                    "is_valid": False,
                    "error_type": "PAYLOAD_TAMPERED",
                    "corrupted_event_id": event.id,
                    "event_index": idx,
                    "expected_hash": recomputed,
                    "recorded_hash": event.current_hash,
                    "message": f"Integrity failure at event #{event.id}: Payload or metadata has been altered after signing!"
                }

            expected_prev_hash = event.current_hash

        return {
            "is_valid": True,
            "total_events": len(events),
            "head_hash": events[-1].current_hash,
            "message": f"Audit chain verified successfully ({len(events)} events checked. Zero tampering detected)."
        }
