import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.document_type import DocumentType
from src.security.abac import check_submission_clearance
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter()


@router.get("/{submission_id}/classification")
async def get_classification(
    submission_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="view_classification")

    if submission.status not in ("pending_classification", "classified"):
        raise HTTPException(status_code=409, detail=f"Classification not available in status '{submission.status}'")

    doc_type = None
    alternatives = []
    if submission.document_type_id:
        result = await db.execute(select(DocumentType).where(DocumentType.id == submission.document_type_id))
        doc_type = result.scalar_one_or_none()

        # Fetch alternatives: all active document types except the chosen one
        alt_result = await db.execute(
            select(DocumentType).where(DocumentType.is_active.is_(True), DocumentType.id != submission.document_type_id)
        )
        alternatives = [
            {"document_type_id": str(dt.id), "name": dt.name, "confidence": 0.05}
            for dt in alt_result.scalars().all()[:3]
        ]

    return {
        "submission_id": str(submission_id),
        "classification": {
            "document_type_id": str(submission.document_type_id) if submission.document_type_id else None,
            "document_type_name": doc_type.name if doc_type else None,
            "confidence": float(submission.classification_confidence) if submission.classification_confidence else None,
            "alternatives": alternatives,
        },
        "template_data": submission.template_data,
        "ai_summary": submission.ai_summary,
        "ai_summary_is_ai_generated": submission.ai_summary is not None,
        "entities": (submission.template_data or {}).get("_entities"),
    }


class ConfirmClassificationRequest(BaseModel):
    document_type_id: uuid.UUID
    template_data: dict | None = None
    classification_method: str = "ai_confirmed"


@router.post("/{submission_id}/confirm-classification")
async def confirm_classification(
    submission_id: uuid.UUID,
    body: ConfirmClassificationRequest,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="confirm_classification")

    if submission.status not in ("pending_classification", "classified"):
        raise HTTPException(status_code=409, detail=f"Cannot confirm classification in status '{submission.status}'")

    # Verify document type exists
    result = await db.execute(select(DocumentType).where(DocumentType.id == body.document_type_id))
    doc_type = result.scalar_one_or_none()
    if doc_type is None:
        raise HTTPException(status_code=404, detail="Document type not found")

    submission.document_type_id = body.document_type_id
    submission.classification_method = body.classification_method
    if body.template_data:
        submission.template_data = body.template_data
    submission.status = "classified"

    await db.commit()
    return {"submission_id": str(submission_id), "status": "classified", "document_type_name": doc_type.name}
