import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.department import Department
from src.models.document_type import DocumentType
from src.models.routing_rule import RoutingRule
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter(prefix="/v1/staff/admin/routing-rules", tags=["admin-routing-rules"])


class RoutingRuleCreate(BaseModel):
    document_type_id: uuid.UUID
    department_id: uuid.UUID
    step_order: int
    expected_duration_hours: int | None = None
    required_clearance_level: int = 0


class RoutingRuleUpdate(BaseModel):
    expected_duration_hours: int | None = None
    required_clearance_level: int | None = None


@router.get("")
async def list_routing_rules(
    document_type_id: uuid.UUID | None = None,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    query = select(RoutingRule).order_by(RoutingRule.document_type_id, RoutingRule.step_order)
    if document_type_id:
        query = query.where(RoutingRule.document_type_id == document_type_id)

    result = await db.execute(query)
    items = result.scalars().all()

    # Resolve department names
    dept_ids = {r.department_id for r in items}
    dept_result = await db.execute(select(Department).where(Department.id.in_(dept_ids)))
    dept_map = {d.id: d.name for d in dept_result.scalars().all()}

    return {
        "items": [
            {
                "id": str(r.id),
                "document_type_id": str(r.document_type_id),
                "department_id": str(r.department_id),
                "department_name": dept_map.get(r.department_id, "Unknown"),
                "step_order": r.step_order,
                "expected_duration_hours": r.expected_duration_hours,
                "required_clearance_level": r.required_clearance_level,
            }
            for r in items
        ]
    }


@router.post("", status_code=201)
async def create_routing_rule(
    body: RoutingRuleCreate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    # Validate references
    dt_result = await db.execute(select(DocumentType).where(DocumentType.id == body.document_type_id))
    if not dt_result.scalar_one_or_none():
        raise HTTPException(404, "Document type not found")

    dept_result = await db.execute(select(Department).where(Department.id == body.department_id))
    if not dept_result.scalar_one_or_none():
        raise HTTPException(404, "Department not found")

    rule = RoutingRule(
        document_type_id=body.document_type_id,
        department_id=body.department_id,
        step_order=body.step_order,
        expected_duration_hours=body.expected_duration_hours,
        required_clearance_level=body.required_clearance_level,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": str(rule.id), "step_order": rule.step_order}


@router.put("/{rule_id}")
async def update_routing_rule(
    rule_id: uuid.UUID,
    body: RoutingRuleUpdate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RoutingRule).where(RoutingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Routing rule not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await db.commit()
    return {"id": str(rule.id), "step_order": rule.step_order}


@router.delete("/{rule_id}")
async def delete_routing_rule(
    rule_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RoutingRule).where(RoutingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Routing rule not found")

    await db.delete(rule)
    await db.commit()
    return {"status": "deleted", "id": str(rule_id)}
