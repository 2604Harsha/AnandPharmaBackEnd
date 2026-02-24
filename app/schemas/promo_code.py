# schemas/promo_code.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PromoCodeCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: int
    max_usage: int
    expires_at: datetime
    status: Optional[str] = "active"


class PromoCodeUpdate(BaseModel):
    discount_type: Optional[str] = None
    discount_value: Optional[int] = None
    max_usage: Optional[int] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None


class PromoCodeOut(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: int
    used_count: int
    max_usage: int
    expires_at: datetime
    status: str

    class Config:
        from_attributes = True