from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleListResponse, RuleResponse, RuleUpdate

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.get("", response_model=RuleListResponse)
async def list_rules(
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Rule.id)))).scalar_one()
    result = await db.execute(select(Rule).order_by(Rule.created_at.desc()))
    rules = result.scalars().all()
    return RuleListResponse(
        items=[RuleResponse.model_validate(r) for r in rules],
        total=total,
    )


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
):
    rule = Rule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()
