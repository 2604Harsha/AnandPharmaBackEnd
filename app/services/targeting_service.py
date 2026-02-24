# services/targeting_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.targetting_rule import AudienceTargetingRule
from schemas.targeting_rule import TargetingRuleCreate, TargetingRuleUpdate


async def create_rule(db: AsyncSession, data: TargetingRuleCreate):
    rule = AudienceTargetingRule(**data.dict())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_rules_by_campaign(db: AsyncSession, campaign_id: int):
    result = await db.execute(
        select(AudienceTargetingRule).where(
            AudienceTargetingRule.campaign_id == campaign_id
        )
    )
    return result.scalars().all()


async def update_rule(db: AsyncSession, rule_id: int, data: TargetingRuleUpdate):
    result = await db.execute(
        select(AudienceTargetingRule).where(
            AudienceTargetingRule.id == rule_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_rule(db: AsyncSession, rule_id: int):
    result = await db.execute(
        select(AudienceTargetingRule).where(
            AudienceTargetingRule.id == rule_id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return None

    await db.delete(rule)
    await db.commit()
    return True