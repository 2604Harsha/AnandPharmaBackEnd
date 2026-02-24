# schemas/targeting_rule.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TargetingRuleCreate(BaseModel):
    campaign_id: int
    field: str
    operator: str
    value: str


class TargetingRuleUpdate(BaseModel):
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None


class TargetingRuleOut(BaseModel):
    id: int
    campaign_id: int
    field: str
    operator: str
    value: str
    created_at: datetime

    class Config:
        from_attributes = True