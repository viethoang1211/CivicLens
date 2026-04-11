import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.case_type import CaseType, CaseTypeRoutingStep
from src.models.department import Department
from src.models.document_requirement import DocumentRequirementGroup, DocumentRequirementSlot
from src.models.document_type import DocumentType
from src.models.dossier import Dossier
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter(prefix="/v1/staff/admin/case-types", tags=["admin-case-types"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SlotCreate(BaseModel):
    document_type_id: uuid.UUID
    label_override: str | None = None


class GroupCreate(BaseModel):
    group_order: int
    label: str
    is_mandatory: bool = True
    slots: list[SlotCreate]

    @field_validator("slots")
    @classmethod
    def slots_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Each requirement group must have at least one slot")
        return v


class RoutingStepCreate(BaseModel):
    step_order: int
    department_id: uuid.UUID
    expected_duration_hours: int | None = None
    required_clearance_level: int = 0


class CaseTypeCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    retention_years: int = 5
    retention_permanent: bool = False
    requirement_groups: list[GroupCreate]
    routing_steps: list[RoutingStepCreate]


class CaseTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    retention_years: int | None = None
    retention_permanent: bool | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(staff: StaffIdentity) -> None:
    if staff.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


async def _load_case_type_or_404(case_type_id: uuid.UUID, db: AsyncSession) -> CaseType:
    result = await db.execute(
        select(CaseType)
        .where(CaseType.id == case_type_id)
        .options(
            selectinload(CaseType.requirement_groups).selectinload(DocumentRequirementGroup.slots).selectinload(
                DocumentRequirementSlot.document_type
            ),
            selectinload(CaseType.routing_steps).selectinload(CaseTypeRoutingStep.department),
        )
    )
    ct = result.scalar_one_or_none()
    if ct is None:
        raise HTTPException(status_code=404, detail="Case type not found")
    return ct


def _serialize_case_type(ct: CaseType) -> dict:
    return {
        "id": str(ct.id),
        "name": ct.name,
        "code": ct.code,
        "description": ct.description,
        "is_active": ct.is_active,
        "retention_years": ct.retention_years,
        "retention_permanent": ct.retention_permanent,
        "requirement_groups": [
            {
                "id": str(g.id),
                "group_order": g.group_order,
                "label": g.label,
                "is_mandatory": g.is_mandatory,
                "slots": [
                    {
                        "id": str(s.id),
                        "document_type_id": str(s.document_type_id),
                        "document_type_code": s.document_type.code if s.document_type else None,
                        "label_override": s.label_override,
                    }
                    for s in g.slots
                ],
            }
            for g in sorted(ct.requirement_groups, key=lambda g: g.group_order)
        ],
        "routing_steps": [
            {
                "id": str(rs.id),
                "step_order": rs.step_order,
                "department_id": str(rs.department_id),
                "department_name": rs.department.name if rs.department else None,
                "expected_duration_hours": rs.expected_duration_hours,
                "required_clearance_level": rs.required_clearance_level,
            }
            for rs in sorted(ct.routing_steps, key=lambda s: s.step_order)
        ],
        "created_at": ct.created_at.isoformat(),
        "updated_at": ct.updated_at.isoformat(),
    }


async def _create_groups_and_slots(
    case_type_id: uuid.UUID, groups: list[GroupCreate], db: AsyncSession, dt_map: dict
) -> None:
    for group_data in groups:
        group = DocumentRequirementGroup(
            case_type_id=case_type_id,
            group_order=group_data.group_order,
            label=group_data.label,
            is_mandatory=group_data.is_mandatory,
        )
        db.add(group)
        await db.flush()
        for slot_data in group_data.slots:
            if slot_data.document_type_id not in dt_map:
                raise HTTPException(status_code=404, detail=f"Document type {slot_data.document_type_id} not found")
            slot = DocumentRequirementSlot(
                group_id=group.id,
                document_type_id=slot_data.document_type_id,
                label_override=slot_data.label_override,
            )
            db.add(slot)


async def _create_routing_steps(
    case_type_id: uuid.UUID, steps: list[RoutingStepCreate], db: AsyncSession, dept_map: dict
) -> None:
    for step_data in steps:
        if step_data.department_id not in dept_map:
            raise HTTPException(status_code=404, detail=f"Department {step_data.department_id} not found")
        step = CaseTypeRoutingStep(
            case_type_id=case_type_id,
            department_id=step_data.department_id,
            step_order=step_data.step_order,
            expected_duration_hours=step_data.expected_duration_hours,
            required_clearance_level=step_data.required_clearance_level,
        )
        db.add(step)


async def _has_active_dossiers(case_type_id: uuid.UUID, db: AsyncSession) -> bool:
    result = await db.execute(
        select(Dossier.id).where(
            Dossier.case_type_id == case_type_id,
            Dossier.status.in_(["submitted", "in_progress"]),
        )
    )
    return result.first() is not None


# ---------------------------------------------------------------------------
# GET /v1/staff/admin/case-types
# ---------------------------------------------------------------------------

@router.get("")
async def list_case_types(
    active_only: bool = False,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CaseType)
        .options(
            selectinload(CaseType.requirement_groups).selectinload(DocumentRequirementGroup.slots).selectinload(
                DocumentRequirementSlot.document_type
            ),
            selectinload(CaseType.routing_steps).selectinload(CaseTypeRoutingStep.department),
        )
        .order_by(CaseType.name)
    )
    if active_only:
        query = query.where(CaseType.is_active.is_(True))
    result = await db.execute(query)
    items = result.scalars().all()
    return {"items": [_serialize_case_type(ct) for ct in items]}


# ---------------------------------------------------------------------------
# POST /v1/staff/admin/case-types
# ---------------------------------------------------------------------------

@router.post("", status_code=201)
async def create_case_type(
    body: CaseTypeCreate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)

    existing = await db.execute(select(CaseType).where(CaseType.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="case_type_code_conflict")

    # Validate dept and doc type references
    dept_result = await db.execute(select(Department))
    dept_map = {d.id: d for d in dept_result.scalars().all()}
    dt_result = await db.execute(select(DocumentType))
    dt_map = {dt.id: dt for dt in dt_result.scalars().all()}

    case_type = CaseType(
        name=body.name,
        code=body.code,
        description=body.description,
        retention_years=body.retention_years,
        retention_permanent=body.retention_permanent,
    )
    db.add(case_type)
    await db.flush()

    await _create_groups_and_slots(case_type.id, body.requirement_groups, db, dt_map)
    await _create_routing_steps(case_type.id, body.routing_steps, db, dept_map)

    await db.commit()
    return {"id": str(case_type.id), "code": case_type.code, "name": case_type.name}


# ---------------------------------------------------------------------------
# GET /v1/staff/admin/case-types/{case_type_id}
# ---------------------------------------------------------------------------

@router.get("/{case_type_id}")
async def get_case_type(
    case_type_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    ct = await _load_case_type_or_404(case_type_id, db)
    return _serialize_case_type(ct)


# ---------------------------------------------------------------------------
# PUT /v1/staff/admin/case-types/{case_type_id}  (metadata only)
# ---------------------------------------------------------------------------

@router.put("/{case_type_id}")
async def update_case_type(
    case_type_id: uuid.UUID,
    body: CaseTypeUpdate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)
    ct = await _load_case_type_or_404(case_type_id, db)
    if body.name is not None:
        ct.name = body.name
    if body.description is not None:
        ct.description = body.description
    if body.retention_years is not None:
        ct.retention_years = body.retention_years
    if body.retention_permanent is not None:
        ct.retention_permanent = body.retention_permanent
    await db.commit()
    await db.refresh(ct)
    return _serialize_case_type(ct)


# ---------------------------------------------------------------------------
# POST /v1/staff/admin/case-types/{case_type_id}/deactivate
# ---------------------------------------------------------------------------

@router.post("/{case_type_id}/deactivate")
async def deactivate_case_type(
    case_type_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)
    ct = await _load_case_type_or_404(case_type_id, db)
    ct.is_active = False
    await db.commit()
    return {"id": str(ct.id), "is_active": False}


# ---------------------------------------------------------------------------
# POST /v1/staff/admin/case-types/{case_type_id}/activate
# ---------------------------------------------------------------------------

@router.post("/{case_type_id}/activate")
async def activate_case_type(
    case_type_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)
    ct = await _load_case_type_or_404(case_type_id, db)
    ct.is_active = True
    await db.commit()
    return {"id": str(ct.id), "is_active": True}


# ---------------------------------------------------------------------------
# PUT /v1/staff/admin/case-types/{case_type_id}/requirement-groups (atomic replace)
# ---------------------------------------------------------------------------

@router.put("/{case_type_id}/requirement-groups")
async def replace_requirement_groups(
    case_type_id: uuid.UUID,
    body: list[GroupCreate],
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)
    ct = await _load_case_type_or_404(case_type_id, db)

    if await _has_active_dossiers(case_type_id, db):
        raise HTTPException(status_code=409, detail="active_dossiers_exist")

    dt_result = await db.execute(select(DocumentType))
    dt_map = {dt.id: dt for dt in dt_result.scalars().all()}

    # Delete existing groups (cascades to slots via FK on delete)
    for group in ct.requirement_groups:
        for slot in group.slots:
            await db.delete(slot)
        await db.delete(group)
    await db.flush()

    await _create_groups_and_slots(case_type_id, body, db, dt_map)
    await db.commit()
    ct = await _load_case_type_or_404(case_type_id, db)
    return _serialize_case_type(ct)


# ---------------------------------------------------------------------------
# PUT /v1/staff/admin/case-types/{case_type_id}/routing-steps (atomic replace)
# ---------------------------------------------------------------------------

@router.put("/{case_type_id}/routing-steps")
async def replace_routing_steps(
    case_type_id: uuid.UUID,
    body: list[RoutingStepCreate],
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(staff)
    ct = await _load_case_type_or_404(case_type_id, db)

    if await _has_active_dossiers(case_type_id, db):
        raise HTTPException(status_code=409, detail="active_dossiers_exist")

    dept_result = await db.execute(select(Department))
    dept_map = {d.id: d for d in dept_result.scalars().all()}

    for step in ct.routing_steps:
        await db.delete(step)
    await db.flush()

    await _create_routing_steps(case_type_id, body, db, dept_map)
    await db.commit()
    ct = await _load_case_type_or_404(case_type_id, db)
    return _serialize_case_type(ct)
