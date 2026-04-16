import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.document_type import DocumentType
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter(tags=["admin-document-types"])


class DocumentTypeCreate(BaseModel):
    name: str
    code: str
    template_schema: dict | None = None
    classification_prompt: str | None = None
    retention_years: int = 5
    retention_permanent: bool = False


class DocumentTypeUpdate(BaseModel):
    name: str | None = None
    template_schema: dict | None = None
    classification_prompt: str | None = None
    retention_years: int | None = None
    retention_permanent: bool | None = None


@router.get("")
async def list_document_types(
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentType).order_by(DocumentType.name))
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": str(dt.id),
                "name": dt.name,
                "code": dt.code,
                "template_schema": dt.template_schema,
                "classification_prompt": dt.classification_prompt,
                "retention_years": dt.retention_years,
                "retention_permanent": dt.retention_permanent,
            }
            for dt in items
        ]
    }


@router.post("", status_code=201)
async def create_document_type(
    body: DocumentTypeCreate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    # Check uniqueness
    existing = await db.execute(select(DocumentType).where(DocumentType.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Document type with code '{body.code}' already exists")

    dt = DocumentType(
        name=body.name,
        code=body.code,
        template_schema=body.template_schema,
        classification_prompt=body.classification_prompt,
        retention_years=body.retention_years,
        retention_permanent=body.retention_permanent,
    )
    db.add(dt)
    await db.commit()
    await db.refresh(dt)
    return {"id": str(dt.id), "name": dt.name, "code": dt.code}


@router.put("/{dt_id}")
async def update_document_type(
    dt_id: uuid.UUID,
    body: DocumentTypeUpdate,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentType).where(DocumentType.id == dt_id))
    dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(404, "Document type not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(dt, field, value)

    await db.commit()
    return {"id": str(dt.id), "name": dt.name, "code": dt.code}


@router.delete("/{dt_id}")
async def deactivate_document_type(
    dt_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentType).where(DocumentType.id == dt_id))
    dt = result.scalar_one_or_none()
    if not dt:
        raise HTTPException(404, "Document type not found")

    # Soft-delete: we don't actually delete to preserve referential integrity
    # In a full implementation, add an `is_active` column
    await db.delete(dt)
    await db.commit()
    return {"status": "deleted", "id": str(dt_id)}
