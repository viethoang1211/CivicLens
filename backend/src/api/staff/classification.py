import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.document_type import DocumentType
from src.security.abac import check_submission_clearance
from src.security.auth import StaffIdentity, get_current_staff
from src.services.routing_service import create_workflow_for_submission

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
    if submission.document_type_id:
        result = await db.execute(select(DocumentType).where(DocumentType.id == submission.document_type_id))
        doc_type = result.scalar_one_or_none()

    # Extract classification metadata from template_data
    td = submission.template_data or {}

    # Build alternatives: prefer AI-generated alternatives, fall back to static list
    ai_alternatives = td.get("_classification_alternatives", [])
    if ai_alternatives and submission.document_type_id:
        # Enrich AI alternatives with document_type_id
        alt_types_result = await db.execute(
            select(DocumentType).where(DocumentType.is_active.is_(True))
        )
        code_to_type = {dt.code: dt for dt in alt_types_result.scalars().all()}
        alternatives = []
        for alt in ai_alternatives[:5]:
            alt_code = alt.get("code")
            alt_dt = code_to_type.get(alt_code)
            if alt_dt and alt_dt.id != submission.document_type_id:
                alternatives.append({
                    "document_type_id": str(alt_dt.id),
                    "name": alt_dt.name,
                    "confidence": float(alt.get("confidence", 0.05)),
                })
    elif submission.document_type_id:
        # Fallback: show other active document types
        alt_result = await db.execute(
            select(DocumentType).where(DocumentType.is_active.is_(True), DocumentType.id != submission.document_type_id)
        )
        alternatives = [
            {"document_type_id": str(dt.id), "name": dt.name, "confidence": 0.05}
            for dt in alt_result.scalars().all()[:3]
        ]
    else:
        alternatives = []

    # Ensemble details for transparency
    ensemble = td.get("_classification_ensemble")

    return {
        "submission_id": str(submission_id),
        "classification": {
            "document_type_id": str(submission.document_type_id) if submission.document_type_id else None,
            "document_type_name": doc_type.name if doc_type else None,
            "confidence": float(submission.classification_confidence) if submission.classification_confidence else None,
            "method": submission.classification_method,
            "alternatives": alternatives,
        },
        "ai_reasoning": {
            "explanation": td.get("_classification_reasoning"),
            "visual_features": td.get("_classification_visual_features", []),
            "key_signals": td.get("_classification_key_signals", []),
            "ensemble_method": td.get("_classification_method"),
            "ensemble_detail": ensemble,
        },
        "template_data": {k: v for k, v in td.items() if not k.startswith("_")} if td else None,
        "ai_summary": submission.ai_summary,
        "ai_summary_is_ai_generated": submission.ai_summary is not None,
        "entities": td.get("_entities"),
        "citizen_check": {
            "citizen_identified": td.get("_citizen_identified", False),
            "is_id_document": td.get("_is_id_document", False),
            "missing_cccd_warning": td.get("_missing_cccd_warning"),
        },
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

    # Auto-route to departments based on the confirmed document type
    routing_result = None
    try:
        routing_result = await create_workflow_for_submission(db, submission)
    except ValueError:
        pass  # No staff with sufficient clearance; leave as classified

    return {
        "submission_id": str(submission_id),
        "status": submission.status,
        "document_type_name": doc_type.name,
        "routing": routing_result,
    }
