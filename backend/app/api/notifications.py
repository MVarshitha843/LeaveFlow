from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.models.notification import Notification
from backend.app.models.employee import Employee
from backend.app.schemas.notification import NotificationResponse
from backend.app.api.deps import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    return db.query(Notification).filter(
        Notification.recipient_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    count = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == 0
    ).count()
    return {"unread_count": count}

@router.post("/{id}/read")
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    notif = db.query(Notification).filter(
        Notification.id == id,
        Notification.recipient_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = 1
    db.commit()
    return {"message": "Notification marked as read"}

@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == 0
    ).update({"is_read": 1})
    db.commit()
    return {"message": "All notifications marked as read"}
