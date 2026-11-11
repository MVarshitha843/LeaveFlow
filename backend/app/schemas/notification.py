from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    recipient_id: str
    title: str
    message: str
    category: str
    is_read: int
    link_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
