import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.case_type import CaseType
from src.models.citizen import Citizen
from src.models.document_requirement import DocumentRequirementGroup, DocumentRequirementSlot
from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.security.auth import StaffIdentity, get_current_staff
from src.services import audit_service, dossier_service
from src.services.oss_client import oss_client
from src.services.quality_service import assess_image_quality

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/staff/dossiers", tags=["staff-dossiers"])

_EDITABLE_STATUSES = {"draft", "scanning"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_dossier_or_404(dossier_id: uuid.UUID, db: AsyncSession) -> Dossier:
    result = await db.execute(
        select(Dossier)
        .where(Dossier.id == dossier_id)
        .options(
            selectinload(Dossier.citizen),
            selectinload(Dossier.case_type).selectinload(CaseType.requirement_groups).selectinload(
                DocumentRequirementGroup.slots
            ).selectinload(DocumentRequirementSlot.document_type),
            selectinload(Dossier.documents).selectinload(DossierDocument.scanned_pages),
            selectinload(Dossier.documents).selectinload(DossierDocument.document_type),
            selectinload(Dossier.documents).selectinload(DossierDocument.requirement_slot).selectinload(
                DocumentRequirementSlot.document_type
            ),
            selectinload(Dossier.workflow_steps),
        )
    )
    dossier = result.scalar_one_or_none()
    if dossier is None:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return dossier


def _build_group_list(dossier: Dossier) -> list[dict]:
    fulfilled_slot_ids = {
        doc.requirement_slot_id
        for doc in dossier.documents
        if doc.requirement_slot_id is not None
    }
    fulfilled_doc_by_slot = {
        doc.requirement_slot_id: doc
        for doc in dossier.documents
        if doc.requirement_slot_id is not None
    }

    groups_out = []
    for group in sorted(dossier.case_type.requirement_groups, key=lambda g: g.group_order):
        slot_ids = {slot.id for slot in group.slots}
        is_fulfilled = bool(slot_ids.intersection(fulfilled_slot_ids))

        slots_out = []
        for slot in group.slots:
            fulfilled_doc = fulfilled_doc_by_slot.get(slot.id)
            slots_out.append({
                "id": str(slot.id),
                "document_type_code": slot.document_type.code if slot.document_type else None,
                "label": slot.label_override or (slot.document_type.name if slot.document_type else str(slot.id)),
                "fulfilled_by_document_id": str(fulfilled_doc.id) if fulfilled_doc else None,
            })

        groups_out.append({
            "id": str(group.id),
            "group_order": group.group_order,
            "label": group.label,
            "is_mandatory": group.is_mandatory,
            "is_fulfilled": is_fulfilled,
            "slots": slots_out,
        })
    return groups_out


def _build_document_list(dossier: Dossier) -> list[dict]:
    docs_out = []
    for doc in dossier.documents:
        docs_out.append({
            "id": str(doc.id),
            "dossier_id": str(dossier.id),
            "requirement_slot_id": str(doc.requirement_slot_id) if doc.requirement_slot_id else None,
            "document_type_id": str(doc.document_type_id) if doc.document_type_id else None,
            "document_type_name": doc.document_type.name if doc.document_type else (
                doc.requirement_slot.label_override or doc.requirement_slot.document_type.name
                if doc.requirement_slot and doc.requirement_slot.document_type
                else None
            ),
            "ai_match_result": doc.ai_match_result,
            "ai_match_overridden": doc.ai_match_overridden,
            "staff_notes": doc.staff_notes,
            "page_count": len(doc.scanned_pages),
            "created_at": doc.created_at.isoformat(),
        })
    return docs_out


def _build_dossier_response(dossier: Dossier, completeness: dict | None = None) -> dict:
    workflow_steps_out = [
        {
            "step_order": ws.step_order,
            "department_id": str(ws.department_id),
            "status": ws.status,
            "started_at": ws.started_at.isoformat() if ws.started_at else None,
            "completed_at": ws.completed_at.isoformat() if ws.completed_at else None,
            "expected_complete_by": ws.expected_complete_by.isoformat() if ws.expected_complete_by else None,
        }
        for ws in sorted(dossier.workflow_steps, key=lambda s: s.step_order)
    ]

    # Derive current_step and progress counts from workflow_steps
    active_step = next((ws for ws in workflow_steps_out if ws["status"] == "active"), None)
    current_step_out = None
    if active_step:
        current_step_out = {
            "step_order": active_step["step_order"],
            "department_name": active_step.get("department_name", f"Phòng {active_step['step_order']}"),
            "status": active_step["status"],
        }
    total_steps = len(workflow_steps_out)
    completed_steps = sum(1 for ws in workflow_steps_out if ws["status"] == "completed")

    return {
        "id": str(dossier.id),
        "reference_number": dossier.reference_number,
        "status": dossier.status,
        # Flat fields for Flutter DTO compatibility
        "citizen_id": str(dossier.citizen_id) if dossier.citizen_id else None,
        "citizen_name": dossier.citizen.full_name if dossier.citizen else None,
        "case_type_id": str(dossier.case_type_id),
        "case_type_name": dossier.case_type.name if dossier.case_type else None,
        # Also keep nested for backwards compat
        "case_type": {
            "id": str(dossier.case_type_id),
            "code": dossier.case_type.code,
            "name": dossier.case_type.name,
        },
        "security_classification": dossier.security_classification,
        "priority": dossier.priority,
        "rejection_reason": dossier.rejection_reason,
        "requirement_snapshot": dossier.requirement_snapshot,
        "completeness": completeness,
        "requirement_groups": _build_group_list(dossier),
        "documents": _build_document_list(dossier),
        "workflow_steps": workflow_steps_out,
        "current_step": current_step_out,
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "created_at": dossier.created_at.isoformat(),
        "updated_at": dossier.updated_at.isoformat(),
        "submitted_at": dossier.submitted_at.isoformat() if dossier.submitted_at else None,
        "completed_at": dossier.completed_at.isoformat() if dossier.completed_at else None,
    }


# ---------------------------------------------------------------------------
# POST /v1/staff/dossiers — T012
# ---------------------------------------------------------------------------


class _CreateDossierBody(BaseModel):
    citizen_id_number: str | None = None
    case_type_id: uuid.UUID
    security_classification: int = 0
    priority: str = "normal"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dossier(
    body: _CreateDossierBody,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    if body.security_classification < 0 or body.security_classification > 3:
        raise HTTPException(status_code=422, detail="security_classification must be 0–3")
    if body.priority not in ("normal", "urgent"):
        raise HTTPException(status_code=422, detail="priority must be 'normal' or 'urgent'")

    citizen = None
    if body.citizen_id_number:
        citizen_result = await db.execute(select(Citizen).where(Citizen.id_number == body.citizen_id_number))
        citizen = citizen_result.scalar_one_or_none()
        if citizen is None:
            raise HTTPException(status_code=404, detail="Citizen not found. Verify CCCD number.")

    ct_result = await db.execute(
        select(CaseType)
        .where(CaseType.id == body.case_type_id)
        .options(
            selectinload(CaseType.requirement_groups).selectinload(DocumentRequirementGroup.slots).selectinload(
                DocumentRequirementSlot.document_type
            )
        )
    )
    case_type = ct_result.scalar_one_or_none()
    if case_type is None:
        raise HTTPException(status_code=404, detail="Case type not found")
    if not case_type.is_active:
        raise HTTPException(status_code=422, detail="case_type_inactive")

    dossier = Dossier(
        citizen_id=citizen.id if citizen else None,
        submitted_by_staff_id=staff.staff_id,
        case_type_id=case_type.id,
        security_classification=body.security_classification,
        priority=body.priority,
        status="draft",
        requirement_snapshot=await dossier_service.build_requirement_snapshot(case_type, db),
    )
    db.add(dossier)
    await db.commit()
    await db.refresh(dossier)

    # Re-load with relationships for response
    dossier = await _load_dossier_or_404(dossier.id, db)
    completeness = await dossier_service.check_completeness(dossier.id, db)
    return _build_dossier_response(dossier, completeness)


# ---------------------------------------------------------------------------
# GET /v1/staff/dossiers — T016
# ---------------------------------------------------------------------------

@router.get("")
async def list_dossiers(
    status_filter: str | None = Query(None, alias="status"),
    case_type_id: uuid.UUID | None = None,
    citizen_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Dossier)
        .options(
            selectinload(Dossier.citizen),
            selectinload(Dossier.case_type),
            selectinload(Dossier.workflow_steps),
        )
        .order_by(Dossier.created_at.desc())
    )
    if status_filter:
        query = query.where(Dossier.status == status_filter)
    if case_type_id:
        query = query.where(Dossier.case_type_id == case_type_id)
    if citizen_id:
        query = query.where(Dossier.citizen_id == citizen_id)

    await db.execute(select(Dossier.id).where(*query.whereclause_list if hasattr(query, 'whereclause_list') else []))
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    dossiers = result.scalars().all()

    items = []
    for d in dossiers:
        active_step = next(
            (ws for ws in sorted(d.workflow_steps, key=lambda s: s.step_order) if ws.status == "active"),
            None,
        )
        items.append({
            "id": str(d.id),
            "reference_number": d.reference_number,
            "status": d.status,
            "citizen_name": d.citizen.full_name if d.citizen else "",
            "case_type_name": d.case_type.name if d.case_type else None,
            "priority": d.priority,
            "created_at": d.created_at.isoformat(),
            "submitted_at": d.submitted_at.isoformat() if d.submitted_at else None,
            "current_department_id": str(active_step.department_id) if active_step else None,
        })

    return {"page": page, "page_size": page_size, "items": items}


# ---------------------------------------------------------------------------
# GET /v1/staff/dossiers/{dossier_id} — T013
# ---------------------------------------------------------------------------

@router.get("/{dossier_id}")
async def get_dossier(
    dossier_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    dossier = await _load_dossier_or_404(dossier_id, db)
    completeness = await dossier_service.check_completeness(dossier_id, db)
    return _build_dossier_response(dossier, completeness)


# ---------------------------------------------------------------------------
# POST /v1/staff/dossiers/{dossier_id}/documents — T014
# ---------------------------------------------------------------------------

@router.post("/{dossier_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    dossier_id: uuid.UUID,
    requirement_slot_id: uuid.UUID = Form(...),
    staff_notes: str | None = Form(None),
    pages: list[UploadFile] = File(...),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    if len(pages) > 30:
        raise HTTPException(status_code=422, detail="Maximum 30 pages per document")

    dossier = await _load_dossier_or_404(dossier_id, db)

    if dossier.status not in _EDITABLE_STATUSES:
        raise HTTPException(status_code=422, detail="dossier_not_editable")

    # Validate slot belongs to this case type
    slot_result = await db.execute(
        select(DocumentRequirementSlot)
        .join(DocumentRequirementGroup)
        .where(
            DocumentRequirementSlot.id == requirement_slot_id,
            DocumentRequirementGroup.case_type_id == dossier.case_type_id,
        )
    )
    slot = slot_result.scalar_one_or_none()
    if slot is None:
        raise HTTPException(status_code=422, detail="slot_not_in_case_type")

    # Check slot not already fulfilled
    existing_doc = await db.execute(
        select(DossierDocument).where(
            DossierDocument.dossier_id == dossier_id,
            DossierDocument.requirement_slot_id == requirement_slot_id,
        )
    )
    if existing_doc.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="slot_already_fulfilled")

    # Create DossierDocument record
    dossier_doc = DossierDocument(
        dossier_id=dossier_id,
        requirement_slot_id=requirement_slot_id,
        document_type_id=slot.document_type_id,
        staff_notes=staff_notes,
    )
    db.add(dossier_doc)
    await db.flush()

    # Upload each page
    pages_out = []
    for idx, page_file in enumerate(pages, start=1):
        image_data = await page_file.read()

        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="file_too_large")

        quality_result = assess_image_quality(image_data)
        if not quality_result["acceptable"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "image_quality_low",
                    "message": f"Page {idx} quality score {quality_result['score']:.2f} below threshold.",
                    "quality_score": quality_result["score"],
                    "guidance": quality_result["guidance"],
                },
            )

        oss_key = f"dossier/{dossier_id}/doc/{dossier_doc.id}/p{idx:03d}.jpg"
        oss_client.upload(oss_key, image_data)

        scanned_page = ScannedPage(
            dossier_document_id=dossier_doc.id,
            page_number=idx,
            image_oss_key=oss_key,
            image_quality_score=quality_result["score"],
            synced_at=datetime.now(UTC),
        )
        db.add(scanned_page)
        pages_out.append({"page_number": idx, "oss_key": oss_key, "quality_score": quality_result["score"]})

    # Advance dossier status
    if dossier.status == "draft":
        dossier.status = "scanning"

    await db.commit()

    # Enqueue AI slot validation
    try:
        from src.workers.classification_worker import validate_document_slot
        validate_document_slot.delay(str(dossier_doc.id))
    except Exception:
        logger.exception("AI validation enqueue failed")

    return {
        "id": str(dossier_doc.id),
        "dossier_id": str(dossier_id),
        "requirement_slot_id": str(requirement_slot_id),
        "document_type_id": str(slot.document_type_id) if slot.document_type_id else None,
        "document_type_name": slot.document_type.name if slot.document_type else None,
        "ai_match_result": None,
        "ai_match_overridden": False,
        "staff_notes": dossier_doc.staff_notes,
        "page_count": len(pages_out),
        "pages": pages_out,
        "created_at": dossier_doc.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# DELETE /v1/staff/dossiers/{dossier_id}/documents/{document_id} — T015
# ---------------------------------------------------------------------------

@router.delete("/{dossier_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    dossier_id: uuid.UUID,
    document_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    dossier_result = await db.execute(select(Dossier).where(Dossier.id == dossier_id))
    dossier = dossier_result.scalar_one_or_none()
    if dossier is None:
        raise HTTPException(status_code=404, detail="Dossier not found")
    if dossier.status not in _EDITABLE_STATUSES:
        raise HTTPException(status_code=422, detail="dossier_not_editable")

    doc_result = await db.execute(
        select(DossierDocument)
        .where(DossierDocument.id == document_id, DossierDocument.dossier_id == dossier_id)
        .options(selectinload(DossierDocument.scanned_pages))
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete stored files
    for page in doc.scanned_pages:
        try:
            if hasattr(oss_client, 'delete'):
                oss_client.delete(page.image_oss_key)
            elif hasattr(oss_client, 'bucket'):
                oss_client.bucket.delete_object(page.image_oss_key)
        except Exception:
            logger.exception("Failed to delete stored file %s", page.image_oss_key)
        await db.delete(page)

    await db.delete(doc)
    await db.commit()


# ---------------------------------------------------------------------------
# PATCH /v1/staff/dossiers/{dossier_id}/documents/{document_id}/override-ai — T038
# ---------------------------------------------------------------------------

class _OverrideAiBody(BaseModel):
    staff_notes: str | None = None


@router.patch("/{dossier_id}/documents/{document_id}/override-ai")
async def override_ai(
    dossier_id: uuid.UUID,
    document_id: uuid.UUID,
    body: _OverrideAiBody,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    doc_result = await db.execute(
        select(DossierDocument).where(
            DossierDocument.id == document_id,
            DossierDocument.dossier_id == dossier_id,
        ).options(
            selectinload(DossierDocument.scanned_pages),
            selectinload(DossierDocument.document_type),
        )
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.ai_match_result is None or doc.ai_match_result.get("match", True):
        raise HTTPException(
            status_code=422,
            detail="override-ai only applicable when AI flagged a mismatch",
        )

    doc.ai_match_overridden = True
    if body.staff_notes is not None:
        doc.staff_notes = body.staff_notes
    await db.commit()
    await db.refresh(doc)

    return {
        "id": str(doc.id),
        "dossier_id": str(dossier_id),
        "requirement_slot_id": str(doc.requirement_slot_id) if doc.requirement_slot_id else None,
        "document_type_id": str(doc.document_type_id) if doc.document_type_id else None,
        "document_type_name": doc.document_type.name if doc.document_type else None,
        "ai_match_result": doc.ai_match_result,
        "ai_match_overridden": doc.ai_match_overridden,
        "staff_notes": doc.staff_notes,
        "page_count": len(doc.scanned_pages),
        "created_at": doc.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /v1/staff/dossiers/{dossier_id}/submit — T028
# ---------------------------------------------------------------------------

@router.post("/{dossier_id}/submit")
async def submit_dossier(
    dossier_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    dossier = await _load_dossier_or_404(dossier_id, db)

    if dossier.status not in ("draft", "scanning", "ready"):
        raise HTTPException(status_code=422, detail="already_submitted")

    completeness = await dossier_service.check_completeness(dossier_id, db)
    if not completeness["complete"]:
        raise HTTPException(
            status_code=422,
            detail={"error": "dossier_incomplete", "missing_groups": completeness["missing_groups"]},
        )

    now = datetime.now(UTC)
    ref_num = await dossier_service.generate_reference_number(db, now.date())

    retention_years = dossier.case_type.retention_years if dossier.case_type else 5

    dossier.reference_number = ref_num
    dossier.status = "submitted"
    dossier.submitted_at = now
    if not dossier.case_type.retention_permanent:
        dossier.retention_expires_at = now.replace(year=now.year + retention_years)

    await db.flush()

    routing_result = await dossier_service.create_dossier_workflow(dossier, db)

    if routing_result["status"] != "pending_routing":
        dossier.status = "in_progress"

    await db.commit()

    await audit_service.log_access(
        db=db,
        actor_type="staff",
        actor_id=staff.staff_id,
        action="dossier_submit",
        resource_type="dossier",
        resource_id=dossier_id,
        metadata={"reference_number": ref_num, "status": dossier.status},
    )

    # Trigger dossier-level AI summary generation
    try:
        from src.workers.summarization_worker import generate_dossier_summary
        generate_dossier_summary.delay(str(dossier_id))
    except Exception:
        logger.exception("Dossier summarization enqueue failed")

    # Reload full dossier with relationships for response
    dossier = await _load_dossier_or_404(dossier_id, db)
    return _build_dossier_response(dossier)


# ---------------------------------------------------------------------------
# PATCH /v1/staff/dossiers/{dossier_id} — T046: priority update
# ---------------------------------------------------------------------------

class _DossierPatchBody(BaseModel):
    priority: str | None = None

    @validator("priority")
    @classmethod
    def _valid_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "normal", "high", "urgent"):
            raise ValueError("priority must be low/normal/high/urgent")
        return v


@router.patch("/{dossier_id}")
async def patch_dossier(
    dossier_id: uuid.UUID,
    body: _DossierPatchBody,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    dossier = await _load_dossier_or_404(dossier_id, db)

    if body.priority is not None:
        dossier.priority = body.priority

    await db.commit()
    await db.refresh(dossier)

    return {
        "id": str(dossier.id),
        "priority": dossier.priority,
        "status": dossier.status,
        "reference_number": dossier.reference_number,
    }
