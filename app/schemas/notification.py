from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True