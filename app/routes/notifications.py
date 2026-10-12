from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import get_notifications, mark_notification_read

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("")
def list_user_notifications(recipient_email: Optional[str] = None, limit: int = Query(50, ge=1, le=100)):
    return get_notifications(recipient_email=recipient_email, limit=limit)

@router.post("/{notification_id}/read")
def mark_read(notification_id: int):
    success = mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read", "id": notification_id}
