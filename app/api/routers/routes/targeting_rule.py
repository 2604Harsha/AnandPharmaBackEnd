# routers/targeting_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.rbac import require_role
from core.database import get_db
from schemas.targeting_rule import (
    TargetingRuleCreate,
    TargetingRuleUpdate,
    TargetingRuleOut,
)
from services.targeting_service import (
    create_rule,
    get_rules_by_campaign,
    update_rule,
    delete_rule,
)

router = APIRouter(prefix="/targeting-rules", tags=["Targeting Rules"])


# ✅ CREATE
@router.post("/", response_model=TargetingRuleOut)
async def create_targeting_rule(
    data: TargetingRuleCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    return await create_rule(db, data)


# ✅ GET BY CAMPAIGN
@router.get("/{campaign_id}", response_model=List[TargetingRuleOut])
async def list_targeting_rules(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    return await get_rules_by_campaign(db, campaign_id)


# ✅ UPDATE
@router.put("/{rule_id}", response_model=TargetingRuleOut)
async def update_targeting_rule(
    rule_id: int,
    data: TargetingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    rule = await update_rule(db, rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


# ✅ DELETE
@router.delete("/{rule_id}")
async def delete_targeting_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    success = await delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted successfully"}